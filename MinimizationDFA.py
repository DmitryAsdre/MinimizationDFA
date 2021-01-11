#!/usr/bin/env python
# coding: utf-8

# In[553]:


#import numpy as np
#port networkx as nx
import matplotlib.pyplot as plt
import sys
from collections import defaultdict
import copy


# In[616]:


import xml.etree.ElementTree as ET
from graphviz import Digraph
from PIL import Image
import itertools
import sys


# In[611]:


class DFA():
    def __init__(self, dfa=None):
        if dfa is None:
            self.nodes = defaultdict(lambda: defaultdict(list))
            self.alphabet = []
            self.states = []
            self.initial = None
            self.final = set()
            self.inversed_nodes = None
        else:
            self.nodes = copy.deepcopy(dfa.nodes)
            self.alphabet = copy.deepcopy(dfa.alphabet)
            self.states = copy.deepcopy(dfa.states)
            self.initial = copy.deepcopy(dfa.initial)
            self.final = copy.deepcopy(dfa.final)
            self.inversed_nodes = copy.deepcopy(dfa.inversed_nodes)
    
    def read_xml(self, name_of_file):
        self.__init__()
        with open(name_of_file, 'r') as f:
            xml = f.read()
            root = ET.fromstring(xml)
            if len(root.findall('state')) == 0:
                raise RuntimeError("Cannot find any state in xml file!");
            for state in root.findall('state'):
                self.states.append(state.attrib['name'])
                cur_name = state.attrib['name']
                if state.attrib['initial'] == "true":
                    if not (self.initial is None):
                        raise RuntimeError("Several initial states")
                    self.initial = cur_name
                if state.attrib['final'] == "true":
                    self.final.add(cur_name);
                for transfer in state.findall('transfer'):
                    self.alphabet.append(transfer.attrib['signal'])
                    self.nodes[cur_name][transfer.attrib['signal']].append(transfer.attrib['destination'])
                    self.states.append(transfer.attrib['destination'])
        if self.initial is None:
            raise RuntimeError("No initial state")
        if len(self.final) == 0:
            raise RuntimeError("No final state")
        self.alphabet = sorted(list(set(self.alphabet)))
        self.states = sorted(list(set(self.states)))
    
    def get_image(self, filename='trash/tmp'):
        if self.initial is None:
            raise RuntimeError("Read automaton from file")
        g = Digraph('G', filename=filename, engine='circo', format='png')
        g.node(self.initial, label=self.initial, _attributes={'shape':'diamond'})
        for name in self.final:
            g.node(name, label=name, _attributes={'color':'red', 'style':'filled'})
        for node_name in self.nodes:
            for signal in self.nodes[node_name]:
                for node_dest in self.nodes[node_name][signal]:
                    g.edge(node_name, node_dest, label=signal)
        g.render()
        return Image.open(filename + '.png')
    
    
    def get_inversed_nodes(self):
        self.inversed_nodes = defaultdict(lambda: defaultdict(list))
        for node in self.nodes:
            for signal in self.nodes[node]:
                for dest_node in self.nodes[node][signal]:
                    self.inversed_nodes[dest_node][signal].append(node)
        return self.inversed_nodes
    
    def build_table(self):
        self.get_inversed_nodes()
        table = dict([((self.states[i], self.states[j]), 0) for i, j in itertools.product(range(len(self.states)), range(len(self.states)))])
        queue = []
        for state1 in self.states:
            for f_state in self.final:
                if state1 not in self.final:
                    table[(state1, f_state)] = 1
                    table[(f_state, state1)] = 1
                    queue.append((state1, f_state))
        while(len(queue) != 0):
            state1, state2 = queue.pop(0)
            for c in self.alphabet:
                for state_1, state_2 in itertools.product(self.inversed_nodes[state1][c], self.inversed_nodes[state2][c]):
                    if(table[(state_1, state_2)] == 0):
                        queue.append((state_1, state_2))
                        table[(state_1, state_2)] = 1
                        table[(state_2, state_1)] = 1
        return table

    def convert_to_minimal_dfa(self):
        table = self.build_table()
        done_states = set()
        old_to_new = {}
        new_states = []
        for state in self.states:
            if state in done_states:
                continue
            done_states.add(state)
            new_state = state + "'"
            new_states.append(new_state)
            for state2 in self.states:
                if table[(state, state2)] == 0:
                    done_states.add(state2)
                    old_to_new[state2] = new_state
        new_final = set([old_to_new[s] for s in self.final])
        for s in self.final:
            new_final.add(old_to_new[s])
        new_initial = old_to_new[self.initial]
        new_nodes = defaultdict(lambda : defaultdict(list))
        for node in self.nodes:
            for signal in self.nodes[node]:
                new_nodes[old_to_new[node]][signal] = [old_to_new[s] for s in self.nodes[node][signal]]
        self.initial = new_initial
        self.final = new_final
        self.states = new_states
        self.nodes = new_nodes
        
    def dfs(self, set_achiev, cur_name):
        for signal in self.nodes[cur_name]:
            for node_name in self.nodes[cur_name][signal]:
                if node_name not in set_achiev:
                    set_achiev.add(node_name)
                    self.dfs(set_achiev, node_name)
    def trim(self):
        set_achiev = set()
        set_achiev.add(self.initial)
        self.dfs(set_achiev, self.initial)
        self.nodes = {n:self.nodes[n] for n in set_achiev}
        self.states = list(set_achiev)
        self.final = list(filter(lambda x: x in set_achiev, self.final))
    
    def get_minimal_dfa(self):
        dfa = DFA(self)
        dfa.trim()
        dfa.convert_to_minimal_dfa()
        return dfa  


# In[ ]:


if __name__ == "__main__":
    arguments = len(sys.argv) - 1
    if arguments != 1:
        raise RuntimeError("Invalid args")
    dfa = DFA()
    dfa.read_xml(sys.argv[1])
    image_first = dfa.get_image()
    #plt.canvas.set_window_title("Initial automaton")
    plt.figure("Initial Automaton")
    plt.imshow(dfa.get_image())
    plt.figure("Minimal Automaton")
    plt.imshow(dfa.get_minimal_dfa().get_image())
    plt.show()
