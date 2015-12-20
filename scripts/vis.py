from IPython.display import IFrame
import json
import os
import sys
import uuid


def vis_network(nodes, edges, physics=False):
    html = """
    <html>
    <head>
      <script type="text/javascript" src="../lib/vis/dist/vis.js"></script>
      <link href="../lib/vis/dist/vis.css" rel="stylesheet" type="text/css">
    </head>
    <body>

    <div id="{id}"></div>

    <script type="text/javascript">
      var nodes = {nodes};
      var groups = {groups};
      var edges = {edges};

      var container = document.getElementById("{id}");
      
      var data = {{
        nodes: nodes,
        edges: edges
      }};

      var options = {{
          nodes: {{
              shape: 'dot',
              size: 25,
              font: {{
                  size: 14
              }}
          }},
          groups: groups,
          edges: {{
              font: {{
                  size: 14,
                  align: 'middle'
              }},
              arrows: {{
                  to: {{enabled: true, scaleFactor: 2}}
              }},
              smooth: {{enabled: false}}
          }},
          physics: {{
              enabled: {physics}
          }}
      }};
      
      var network = new vis.Network(container, data, options);

    </script>
    </body>
    </html>
    """

    black = "#000000"
    dark_gray = "#333333"
    medium_gray = "#888888"
    light_gray = "#cccccc"
    white = "#ffffff"
    dark_green = "#7b9f35"
    light_green = "#d4ee9f"
    dark_purple = "#582a72"
    light_purple = "#9775aa"
    dark_red = "#aa3939"
    light_red = "#ffaaaa"

    groups = {
        'Element': {
            'color': {
                'border': dark_gray, 'background': dark_gray,
                'highlight': {
                    'border': dark_gray, 'background': dark_gray}}},
        'Connection': {
            'color': {
                'border': medium_gray, 'background': white,
                'highlight': {
                    'border': medium_gray, 'background': white}}},
        "Metamodel Element": {
            'color': {
                'border': dark_green, 'background': dark_green,
                'highlight': {
                    'border': dark_gray, 'background': dark_green}}},
        "Metamodel Connection": {
            'color': {
                'border': light_green, 'background': light_green,
                'highlight': {
                    'border': dark_gray, 'background': light_green}}},
        "Model Element": {
            'color': {
                'border': dark_purple, 'background': dark_purple,
                'highlight': {
                    'border': dark_gray, 'background': dark_purple}}},
        "Model Connection": {
            'color': {
                'border': light_purple, 'background': light_purple,
                'highlight': {
                    'border': dark_gray, 'background': light_purple}}},
        "Instance Element": {
            'color': {
                'border': dark_red, 'background': dark_red,
                'highlight': {
                    'border': dark_gray, 'background': dark_red}}},
        "Instance Connection": {
            'color': {
                'border': light_red, 'background': light_red,
                'highlight': {
                    'border': dark_gray, 'background': light_red}}},
    }

    unique_id = str(uuid.uuid4())
    html = html.format(id=unique_id, nodes=json.dumps(nodes),
                       groups=json.dumps(groups),
                       edges=json.dumps(edges), physics=json.dumps(physics))
    
    filename = "figure/graph-{}.html".format(unique_id)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as network_file:
        network_file.write(html)

    return IFrame(filename, width="100%", height="400")


# def draw(graph, options, physics=False, limit=100):
def draw(graph, labels=None, physics=True, relax_gray_relationships=False,
         limit=None):
    # The options argument should be a dictionary of node labels and property
    # keys; it determines which property is displayed for the node label.
    # For example, in the movie graph,
    # options = {"Movie": "title", "Person": "name"}.
    # Omitting a node label from the options dict will leave the node unlabeled
    # in the visualization.
    # Setting physics = True makes the nodes bounce around when you touch them!
    if labels:
        query = ("""
        MATCH n
        WHERE {labels}
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        """.format(labels=' OR '.join('n:`{label}`'.format(label=label)
                                      for label in labels)))
    else:
        query = """
        MATCH n
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
    if limit:
        query += """
        LIMIT {limit}
        """.format(limit)

    data = graph.cypher.execute(query)

    nodes = []
    edges = []

    def get_vis_info(node):
        node_label = list(node.labels)[0]
        # prop_key = options.get(node_label)
        prop_key = 'name'
        vis_label = node.properties.get(prop_key, "")
        vis_id = node.ref.split("/")[1]

        title = {}

        for key, value in node.properties.items():
            if sys.version_info <= (3, 0):
                key = key.encode("utf8")
                value = value.encode("utf8")

            title[key] = value

        return {"id": vis_id, "label": vis_label, "group": node_label,
                "title": repr(title)}

    for row in data:
        source = row[0]
        rel = row[1]
        target = row[2]

        source_info = get_vis_info(source)

        if source_info not in nodes:
            nodes.append(source_info)

        if rel:
            target_info = get_vis_info(target)

            if target_info not in nodes:
                nodes.append(target_info)

            source_layer = source_info['group'].split(' ')[0]
            target_layer = target_info['group'].split(' ')[0]
            if (source_layer == target_layer or
                    (source_layer == 'Element' and
                     target_layer == 'Connection')):
                same_model_layer = True
            else:
                same_model_layer = False
            if same_model_layer:
                edge_color = '#333333'
                edge_physics = True
            else:
                edge_color = '#dddddd'
                edge_physics = False if relax_gray_relationships else True

            edges.append({"from": source_info["id"], "to": target_info["id"],
                          "label": rel.type, 'physics': edge_physics,
                          'color': edge_color, 'font': {'color': edge_color}})

    return vis_network(nodes, edges, physics=physics)
