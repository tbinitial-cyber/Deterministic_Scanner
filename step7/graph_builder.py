from .schemas import LineageGraph
from .node_builder import NodeBuilder
from .edge_builder import EdgeBuilder

class GraphBuilder:
    def __init__(self, cookies: list, hosts: list, vendors: list, behaviour_findings: list):
        self.node_builder = NodeBuilder(cookies, hosts, vendors)
        self.edge_builder = EdgeBuilder(behaviour_findings, cookies)
        
    def build(self) -> LineageGraph:
        nodes = []
        nodes.append(self.node_builder.build_browser_node())
        nodes.extend(self.node_builder.build_cookie_nodes())
        nodes.extend(self.node_builder.build_host_nodes())
        nodes.extend(self.node_builder.build_service_nodes())
        nodes.extend(self.node_builder.build_processing_nodes())
        
        edges = self.edge_builder.build_edges(nodes)
        
        return LineageGraph(nodes=nodes, edges=edges)
