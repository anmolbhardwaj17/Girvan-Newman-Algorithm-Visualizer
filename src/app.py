from flask import Flask, redirect, url_for, render_template, request
import networkx as nx
from pyvis.network import Network
from IPython.core.display import display, HTML
from werkzeug.utils import secure_filename
import math
import csv
import random as rand
import sys

_DEBUG_ = False
app = Flask(__name__)


def UpdateDeg(A, nodes):
    deg_dict = {}
    n = len(nodes)  # len(A) ---> some ppl get issues when trying len() on sparse matrixes!
    B = A.sum(axis=1)
    i = 0
    for node_id in list(nodes):
        deg_dict[node_id] = B[i, 0]
        i += 1
    return deg_dict

def CmtyGirvanNewmanStep(G):
    if _DEBUG_:
        print("Running CmtyGirvanNewmanStep method ...")
    init_ncomp = nx.number_connected_components(G)    #no of components
    ncomp = init_ncomp
    while ncomp <= init_ncomp:
        bw = nx.edge_betweenness_centrality(G, weight='weight')    #edge betweenness for G
        #find the edge with max centrality
        max_ = max(bw.values())
        #find the edge with the highest centrality and remove all of them if there is more than one!
        for k, v in bw.items():
            if float(v) == max_:
                G.remove_edge(k[0],k[1])
        ncomp = nx.number_connected_components(G)

def _GirvanNewmanGetModularity(G, deg_, m_):
    New_A = nx.adj_matrix(G)
    New_deg = {}
    New_deg = UpdateDeg(New_A, G.nodes())
    #Let's compute the Q
    comps = nx.connected_components(G)    #list of components
    print('No of communities in decomposed G: {}'.format(nx.number_connected_components(G)))
    Mod = 0    #Modularity of a given partitionning
    for c in comps:
        EWC = 0    #no of edges within a community
        RE = 0    #no of random edges
        for u in c:
            EWC += New_deg[u]
            RE += deg_[u]        #count the probability of a random edge
        Mod += ( float(EWC) - float(RE*RE)/float(2*m_) )
    Mod = Mod/float(2*m_)
    if _DEBUG_:
        print("Modularity: {}".format(Mod))
    return Mod

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/getfile', methods=['GET','POST'])
def getafile():

    if request.method == 'POST':
        result = request.files['myfile']
        result.save(secure_filename(result.filename))
    else:
        result = request.args.get['myfile']

    reader = csv.reader(open(result.filename, "r"))
    g = Network(height='100%', width='100%', heading='', bgcolor="#000000", font_color='#ffffff')
    g.add_nodes(range(100))
    for line in reader:
        g.add_edge(int(line[0]), int(line[1]))

    g.barnes_hut()
    g.show("example.html")
    display(HTML('example.html'))

    G = nx.Graph()
    reader = csv.reader(open(result.filename, "r"))
    for line in reader:
        if len(line) > 2:
            if float(line[2]) != 0.0:

                G.add_edge(int(line[0]), int(line[1]), weight=float(line[2]))
        else:
            # line format: u,v
            G.add_edge(int(line[0]), int(line[1]), weight=1.0)

    if _DEBUG_:
        print('G nodes: {} & G no of nodes: {}'.format(G.nodes(), G.number_of_nodes()))

    n = G.number_of_nodes()  # |V|
    A = nx.adj_matrix(G)  # adjacenct matrix

    m_ = 0.0  # the weighted version for number of edges
    for i in range(0, n):
        for j in range(0, n):
            m_ += A[i, j]
    m_ = m_ / 2.0
    if _DEBUG_:
        print("m: {}".format(m_))

    # calculate the weighted degree for each node
    Orig_deg = {}


    Orig_deg = UpdateDeg(A, G.nodes())

    BestQ = 0.0
    Q = 0.0

    while True:
        CmtyGirvanNewmanStep(G)
        Q = _GirvanNewmanGetModularity(G, Orig_deg, m_);
        print("Modularity of decomposed G: {}".format(Q))
        if Q > BestQ:
            BestQ = Q
            Bestcomps = list(nx.connected_components(G))  # Best Split
            print("Identified components: {}".format(Bestcomps))
        if G.number_of_edges() == 0:
            break
    if BestQ > 0.0:
        print("Max modularity found (Q): {} and number of communities: {}".format(BestQ, len(Bestcomps)))
        maxmodularity = BestQ
        length = len(Bestcomps)
        print("Graph communities: {}".format(Bestcomps))
        graphcoms = Bestcomps
    else:
        print("Max modularity (Q):", BestQ)

    return render_template('view.html', maxmodularity=maxmodularity, graphcoms=graphcoms, length=length)


if __name__ == '__main__':
    app.run()
