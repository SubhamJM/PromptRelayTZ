import re
from typing import Any, Dict, List, Optional
import networkx as nx


class NetworkXDependencyTool:
    """
    Agent 2 Specialized Tool: NetworkX Incident Reconstructor & Dependency Graph.
    Uses NetworkX to structure extracted facts into a directed graph, connect causal events,
    track movements of people and objects across locations, and determine event dependencies.
    """

    def __init__(self):
        self.name = "networkx_graph_tool"
        self.description = "Constructs event dependency graphs and reconstructs incident timelines."

    def build_event_graph(self, extracted_evidence_text: str) -> Dict[str, Any]:
        """
        Parses evidence lines and populates a NetworkX DiGraph.
        """
        G = nx.DiGraph()
        lines = [l.strip() for l in extracted_evidence_text.split("\n") if l.strip()]

        events: List[Dict[str, Any]] = []
        time_pattern = re.compile(r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\b", re.IGNORECASE)

        prev_event_id: Optional[str] = None

        for idx, line in enumerate(lines):
            # Skip report headers/footers
            if "=== " in line:
                continue

            time_match = time_pattern.search(line)
            event_time = time_match.group(1) if time_match else f"Step-{idx+1}"
            event_id = f"EV_{idx+1}"

            is_uncertain = "[UNCERTAIN]" in line or "unclear" in line.lower() or "alleged" in line.lower()

            # Add node
            G.add_node(
                event_id,
                time=event_time,
                description=line[:80],
                status="uncertain" if is_uncertain else "confirmed"
            )

            events.append({
                "id": event_id,
                "time": event_time,
                "description": line,
                "status": "uncertain" if is_uncertain else "confirmed"
            })

            # Add sequential temporal edge
            if prev_event_id:
                G.add_edge(prev_event_id, event_id, relation="precedes")

            # Check for causal or containment connections
            lower = line.lower()
            if any(k in lower for k in ["breach", "alarm", "unauthorized", "loaded", "override", "poison", "stole"]):
                G.nodes[event_id]["critical"] = True
                if prev_event_id:
                    G.add_edge(prev_event_id, event_id, relation="triggers")

            prev_event_id = event_id

        # Graph Metrics
        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()
        
        # Check DAG and topological order
        is_dag = nx.is_directed_acyclic_graph(G)
        sequence: List[str] = []
        if is_dag and node_count > 0:
            try:
                topological_nodes = list(nx.topological_sort(G))
                sequence = [f"{G.nodes[n].get('time', n)}: {G.nodes[n].get('description', '')}" for n in topological_nodes]
            except Exception:
                sequence = [f"{e['time']}: {e['description']}" for e in events]
        else:
            sequence = [f"{e['time']}: {e['description']}" for e in events]

        # Extract critical path or dependencies
        critical_events = [n for n, attr in G.nodes(data=True) if attr.get("critical")]

        return {
            "status": "success",
            "tool_name": self.name,
            "total_nodes": node_count,
            "total_edges": edge_count,
            "is_dag": is_dag,
            "reconstructed_sequence": sequence,
            "critical_event_count": len(critical_events),
            "events": events,
        }

    def run(self, extracted_evidence_text: str) -> str:
        """Runs the NetworkX tool and produces a structured dependency reconstruction."""
        result = self.build_event_graph(extracted_evidence_text)
        output_lines = [
            "=== NETWORKX INCIDENT DEPENDENCY GRAPH ===",
            f"Nodes Analyzed: {result['total_nodes']} | Causal Edges: {result['total_edges']} | Valid DAG: {result['is_dag']}",
            "Reconstructed Event Timeline & Dependencies:",
        ]
        for seq in result["reconstructed_sequence"][:10]:
            output_lines.append(f"  • {seq}")

        output_lines.append(f"Critical Incident Nodes Detected: {result['critical_event_count']}")
        output_lines.append("=== END NETWORKX GRAPH REPORT ===")
        return "\n".join(output_lines)
