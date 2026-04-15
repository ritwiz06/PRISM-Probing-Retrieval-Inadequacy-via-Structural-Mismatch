from __future__ import annotations

from dataclasses import asdict
import pickle
import re
from pathlib import Path
from urllib.parse import quote

import networkx as nx  # type: ignore
from rdflib import Graph, Namespace, URIRef  # type: ignore

from prism.retrievers.base import BaseRetriever
from prism.retrievers.common import tokenize
from prism.schemas import RetrievedItem, Triple

PRISM = Namespace("https://prism.local/kg/")

ENTITY_ALIASES = {
    "mammals": "mammal",
    "mammal": "mammal",
    "bat": "bat",
    "bats": "bat",
    "penguin": "penguin",
    "penguins": "penguin",
    "dolphin": "dolphin",
    "dolphins": "dolphin",
    "cat": "cat",
    "cats": "cat",
    "dog": "dog",
    "dogs": "dog",
    "eagle": "eagle",
    "eagles": "eagle",
    "owl": "owl",
    "owls": "owl",
    "duck": "duck",
    "ducks": "duck",
    "frog": "frog",
    "frogs": "frog",
    "whale": "whale",
    "whales": "whale",
    "salmon": "salmon",
    "fish": "fish",
    "insect": "insect",
    "insects": "insect",
    "ostrich": "ostrich",
    "ostriches": "ostrich",
    "sparrow": "sparrow",
    "sparrows": "sparrow",
    "bird": "bird",
    "birds": "bird",
    "animal": "animal",
    "animals": "animal",
    "vertebrate": "vertebrate",
    "vertebrates": "vertebrate",
    "mosquito": "mosquito",
    "mosquitoes": "mosquito",
    "wing": "wing",
    "wings": "wings",
    "fly": "fly",
    "flight": "fly",
    "swim": "swim",
    "milk": "milk",
    "echolocation": "echolocation",
}

PROPERTY_ALIASES = {
    "fly": "capable_of",
    "flying": "capable_of",
    "able": "capable_of",
    "swim": "capable_of",
    "swimming": "capable_of",
    "eat": "eats",
    "eats": "eats",
    "property": "has_property",
    "allows": "has_property",
    "feature": "has_property",
    "adaptation": "has_property",
    "produce": "produces",
    "produces": "produces",
}

NEGATED_PROPERTIES = {"not_capable_of", "lacks_property"}


class KGRetriever(BaseRetriever):
    backend_name = "kg"

    def __init__(self, triples: list[Triple]) -> None:
        self.triples = triples
        self.triples_by_id = {triple.triple_id: triple for triple in triples}
        self.graph = Graph()
        self.nx_graph = nx.MultiDiGraph()
        self._build_graphs(triples)

    @classmethod
    def build(cls, triples: list[Triple]) -> "KGRetriever":
        return cls(triples)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedItem]:
        candidates = self._template_candidates(query)
        if not candidates:
            candidates = [self._triple_to_item(triple, score=self._lexical_score(query, triple), mode="fallback") for triple in self.triples]
        ranked = sorted(candidates, key=lambda item: (item.score, item.item_id), reverse=True)
        return ranked[:top_k]

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as file:
            pickle.dump({"triples": [asdict(triple) for triple in self.triples]}, file)
        return output_path

    @classmethod
    def load(cls, path: str | Path) -> "KGRetriever":
        with Path(path).open("rb") as file:
            payload = pickle.load(file)
        return cls([Triple(**row) for row in payload["triples"]])

    @classmethod
    def load_jsonl(cls, path: str | Path) -> "KGRetriever":
        from prism.utils import read_jsonl_triples

        return cls(read_jsonl_triples(path))

    def membership_lookup(self, entity: str, klass: str) -> list[RetrievedItem]:
        return [
            self._triple_to_item(triple, score=5.0, mode="membership")
            for triple in self._find_triples(subject=entity, predicate="is_a", object_=klass)
        ]

    def property_lookup(self, entity: str, prop: str, object_: str | None = None) -> list[RetrievedItem]:
        triples = self._find_triples(subject=entity, predicate=prop, object_=object_)
        return [self._triple_to_item(triple, score=5.0, mode="property") for triple in triples]

    def relation_lookup(self, subject: str, predicate: str, object_: str | None = None) -> list[RetrievedItem]:
        triples = self._find_triples(subject=subject, predicate=predicate, object_=object_)
        return [self._triple_to_item(triple, score=5.0, mode="relation") for triple in triples]

    def two_hop_paths(self, source: str, target: str) -> list[RetrievedItem]:
        items: list[RetrievedItem] = []
        if source not in self.nx_graph or target not in self.nx_graph:
            return items
        for mid in self.nx_graph.successors(source):
            if target not in self.nx_graph.successors(mid):
                continue
            first_edges = self.nx_graph.get_edge_data(source, mid) or {}
            second_edges = self.nx_graph.get_edge_data(mid, target) or {}
            for _, first in first_edges.items():
                for _, second in second_edges.items():
                    first_triple = self.triples_by_id[first["triple_id"]]
                    second_triple = self.triples_by_id[second["triple_id"]]
                    items.append(self._path_to_item([first_triple, second_triple], score=6.0, mode="two_hop"))
        return items

    def _template_candidates(self, query: str) -> list[RetrievedItem]:
        lowered = query.lower()
        entities = _entities_in_query(lowered)
        prop = _property_in_query(lowered)
        items: list[RetrievedItem] = []

        if _is_universal_query(lowered) and prop:
            klass = _class_in_query(lowered) or (entities[0] if entities else None)
            if klass:
                items.extend(self._universal_property_items(klass, prop, _object_for_property(lowered, prop)))
                return items

        if "what property" in lowered or "what adaptation" in lowered or "allows" in lowered:
            subject = entities[0] if entities else None
            if subject:
                items.extend(self.property_lookup(subject, "has_property"))
                if "fly" in lowered:
                    items.extend(self.property_lookup(subject, "capable_of", "fly"))
                return items

        if "path" in lowered or "connect" in lowered or "chain" in lowered or "bridge" in lowered or "links" in lowered:
            if len(entities) >= 2:
                items.extend(self.two_hop_paths(entities[0], entities[-1]))
                if not items:
                    direct = self._find_triples(subject=entities[0], object_=entities[-1])
                    items.extend(self._triple_to_item(triple, score=5.5, mode="direct_relation") for triple in direct)
                return items

        if lowered.startswith("is ") or lowered.startswith("are "):
            if len(entities) >= 2:
                items.extend(self.membership_lookup(entities[0], entities[1]))
                if not items:
                    items.extend(self.two_hop_paths(entities[0], entities[1]))
                if items:
                    return items

        if lowered.startswith("can ") or " able to " in lowered:
            subject = _class_in_query(lowered) or (entities[0] if entities else None)
            obj = _object_for_property(lowered, prop or "capable_of")
            if subject and obj:
                items.extend(self._existential_property_items(subject, "capable_of", obj))
                return items

        if lowered.startswith("what eats") and entities:
            object_ = entities[-1]
            return [self._triple_to_item(triple, score=5.0, mode="inverse_relation") for triple in self._find_triples(predicate="eats", object_=object_)]

        if prop and entities:
            subject = entities[0]
            object_ = _object_for_property(lowered, prop)
            items.extend(self.relation_lookup(subject, prop, object_))
            if items:
                return items

        return items

    def _existential_property_items(self, subject_or_class: str, predicate: str, object_: str) -> list[RetrievedItem]:
        items = self.property_lookup(subject_or_class, predicate, object_)
        members = self._members_of_class(subject_or_class)
        for member_id, membership_triple in members:
            supporting = self._find_triples(subject=member_id, predicate=predicate, object_=object_)
            for support in supporting:
                items.append(self._path_to_item([membership_triple, support], score=6.0, mode="existential"))
        return items

    def _universal_property_items(self, klass: str, predicate: str, object_: str | None) -> list[RetrievedItem]:
        items: list[RetrievedItem] = []
        object_ = object_ or "fly"
        for member_id, membership_triple in self._members_of_class(klass):
            counterexamples = self._find_triples(subject=member_id, predicate=f"not_{predicate}", object_=object_)
            if not counterexamples:
                counterexamples = self._find_triples(subject=member_id, predicate="not_capable_of", object_=object_)
            for counterexample in counterexamples:
                items.append(self._path_to_item([membership_triple, counterexample], score=7.0, mode="universal_counterexample"))
            supporting = self._find_triples(subject=member_id, predicate=predicate, object_=object_)
            for support in supporting:
                items.append(self._path_to_item([membership_triple, support], score=4.0, mode="universal_support"))
        return items

    def _members_of_class(self, klass: str) -> list[tuple[str, Triple]]:
        return [(triple.subject, triple) for triple in self._find_triples(predicate="is_a", object_=klass)]

    def _find_triples(
        self,
        subject: str | None = None,
        predicate: str | None = None,
        object_: str | None = None,
    ) -> list[Triple]:
        return [
            triple
            for triple in self.triples
            if (subject is None or triple.subject == subject)
            and (predicate is None or triple.predicate == predicate)
            and (object_ is None or triple.object == object_)
        ]

    def _build_graphs(self, triples: list[Triple]) -> None:
        for triple in triples:
            subject_ref = _uri(triple.subject)
            predicate_ref = _uri(triple.predicate)
            object_ref = _uri(triple.object)
            self.graph.add((subject_ref, predicate_ref, object_ref))
            self.nx_graph.add_edge(
                triple.subject,
                triple.object,
                key=triple.triple_id,
                predicate=triple.predicate,
                triple_id=triple.triple_id,
                source_doc_id=triple.source_doc_id,
            )

    def _triple_to_item(self, triple: Triple, score: float, mode: str) -> RetrievedItem:
        return RetrievedItem(
            item_id=triple.triple_id,
            content=f"{triple.subject} {triple.predicate} {triple.object}",
            score=score,
            source_type="triple",
            metadata={
                "triple_id": triple.triple_id,
                "source_doc_id": triple.source_doc_id,
                "subject": triple.subject,
                "predicate": triple.predicate,
                "object": triple.object,
                "hop_count": "1",
                "backend_type": "kg",
                "query_mode": mode,
            },
        )

    def _path_to_item(self, path: list[Triple], score: float, mode: str) -> RetrievedItem:
        path_id = "path:" + "->".join(triple.triple_id for triple in path)
        return RetrievedItem(
            item_id=path_id,
            content=" ; ".join(f"{triple.subject} {triple.predicate} {triple.object}" for triple in path),
            score=score,
            source_type="path",
            metadata={
                "path_id": path_id,
                "triple_id": ",".join(triple.triple_id for triple in path),
                "source_doc_id": ",".join(triple.source_doc_id for triple in path),
                "subject": path[0].subject,
                "predicate": " -> ".join(triple.predicate for triple in path),
                "object": path[-1].object,
                "hop_count": str(len(path)),
                "backend_type": "kg",
                "query_mode": mode,
            },
        )

    @staticmethod
    def _lexical_score(query: str, triple: Triple) -> float:
        query_tokens = set(tokenize(query))
        triple_tokens = set(tokenize(f"{triple.subject} {triple.predicate} {triple.object}"))
        return len(query_tokens & triple_tokens) / max(1, len(query_tokens))


def _entities_in_query(query: str) -> list[str]:
    matches: list[tuple[int, int, str]] = []
    for alias, entity in ENTITY_ALIASES.items():
        for match in re.finditer(rf"\b{re.escape(alias)}\b", query):
            matches.append((match.start(), -len(alias), entity))
    found: list[str] = []
    for _, _, entity in sorted(matches):
        if entity not in found:
            found.append(entity)
    return found


def _class_in_query(query: str) -> str | None:
    for klass in ("mammal", "bird", "animal", "vertebrate"):
        if re.search(rf"\b{klass}s?\b", query):
            return klass
    return None


def _property_in_query(query: str) -> str | None:
    for alias, prop in PROPERTY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", query):
            return prop
    return None


def _object_for_property(query: str, predicate: str) -> str | None:
    if "fly" in query or "flight" in query:
        return "fly"
    if "swim" in query:
        return "swim"
    if "milk" in query:
        return "milk"
    if "mosquito" in query:
        return "mosquito"
    if predicate == "has_property" and ("wing" in query or "fly" in query):
        return "wings"
    return None


def _is_universal_query(query: str) -> bool:
    return any(marker in query for marker in ("are all", "do all", "can all", "every ", "all "))


def _uri(value: str) -> URIRef:
    return URIRef(PRISM[quote(value.replace(" ", "_"), safe="_")])
