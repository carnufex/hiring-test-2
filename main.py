'''docstring'''

#1. weight letters and symbols? already weighted in binary?
#2. add every line from words.txt to a dictionary as value with key being huffman value
#3 for each word in input look at the dictionary and append its value to new output.
#4 decompile by doing same thing

#using a dict might get very high memory usage.

import re
import heapq

class Node(object):
    def __init__(self, symbol=None, occurances=0):
        self.symbol = symbol
        self.occur = occurances
        self.left_child = None
        self.right_child = None

    def __repr__(self):
        return "Node(Symbol: '{}',Occurances: {})\n".format(self.symbol ,self.occur)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.occur == other.occur
        return False

    def __cmp__(self, other):
        if isinstance(other, Node):
            return self.occur > other.occur

    def __lt__(self, other):
        if isinstance(other, Node):
            return self.occur < other.occur

    def __add__(self, other):
        if isinstance(other, Node):
            node = Node(None, self.occur+other.occur)
            # print("added new node: ", node)
            node.left_child = self
            node.right_child = other
            return node

    def is_leaf(self):
        if self.symbol is not None:
            return True
        return False

class Tree(object):
    SYMBOL_LIMIT = 257
    def __init__(self, dictionary=None):
        if dictionary is not None:
            self.heap = self._build_heap(dictionary)
            self.top_node = self._build_tree()
            self.codes = self._build_code_tree()
            # self.codes = self._build_code_tree()

    def _build_heap(self, dictionary):
        '''building BST from dict'''
        heap = []
        for symbol, occur in dictionary.items():
            node = Node(symbol, occur)
            heapq.heappush(heap, node)
        return heap

    def _build_tree(self):
        while(len(self.heap) > 1):
            left_child, right_child = heapq.heappop(self.heap), heapq.heappop(self.heap)
            parent = left_child + right_child
            heapq.heappush(self.heap, parent)
        #should only be top node left, return it
        return heapq.heappop(self.heap)
    
    def _build_code_tree(self):
        if self.top_node is not None:
            codes = {}
            self._add_codes(self.top_node, '', codes)
        return codes

    def _add_codes(self, current_node, current_code, codes):
        if current_node is not None:
            if current_node.symbol is not None:
                codes[current_node.symbol] = current_code
                print("added updated code: {} to {}".format(current_code, current_node.symbol))
            self._add_codes(current_node.left_child, current_code+'0', codes)
            self._add_codes(current_node.right_child, current_code+'1', codes)

    
class Reader(object):
    def __init__(self, in_file_path="datasheet.txt", vocabulary_file_path='words.txt', output_file_path='output.txt'):
        self.in_file_path = in_file_path
        self.out_file_path = output_file_path
        self.vocabulary_file_path = vocabulary_file_path

    def possible_words(self, file):
        words_dict = {}
        with open(file, 'rb') as data:
            for line in data:
                # word = line.split()
                words = re.split('(\W)', line.decode())
                for word in words:
                    words_dict[word] = 0
        return words_dict

    def word_occurances(self, file, possibilities):
        d = possibilities
        with open(file, 'rb') as data:
            for line in data:
                # words = line.split()
                words = re.split('(\W)', line.decode())
                for word in words:
                    try:
                        d[word] = d[word] + 1
                    except:
                        # Words.txt didnt contain this word/symbol, No requirement seem to be broken by adding it anyhow.
                        d[word] = 1
                        # words with special symbols gets very wierd here
        sorted_dict = sorted(d.items(), key=lambda kv: kv[1], reverse=True)
        return sorted_dict

    def remove_unused_words(self, weighted_words_dict):
        d = {}
        for entry in weighted_words_dict:
            if entry[1] is 0:
                #weighted_words_dict is sorted, when we hit 0 there will only be 0's left.
                return d
            #most likely there will be less than 50% of all possible words used, thus less work to just make a new dict than popping/deleting
            d[entry[0]] = entry[1]
        # all words were used
        return d


class HuffmanEncode(Reader):

    def compress(self):
        print(self.in_file_path)
        with open(self.in_file_path, 'rb') as in_text:
            text = in_text.read()
        in_text.close()

        final_words = self.remove_unused_words(self.word_occurances(self.in_file_path, self.possible_words(self.vocabulary_file_path)))
        tree = Tree(final_words)
        codes_dict = tree.codes

        with open(self.out_file_path, "wb") as out:
            try:
                output = ''
                res = b''
                # out.write(str(codes_dict).encode())
                for key, val in codes_dict.items():
                    out.write(key.encode() + ':'.encode() + val.encode())
                with open(self.in_file_path, "rb") as inp:
                    for line in inp.readlines():
                        words = re.split('(\W)', line.decode())
                        for word in words:
                            output += codes_dict[word]
                while len(output) > 0:
                    out.write(bytes((int(output[:8], 2), )))
                    output = output[8:]
            except Exception as err:
                print("in except", err)
            finally:
                inp.close()
                out.close()

    def int_to_bytes(self, integer):
        return integer.to_bytes((integer.bit_length() + 7) // 8, 'big')

class HuffmanDecode(Reader):

    def decompress(self):
        # print(self.load_vocabulary(self.vocabulary_file_path))
        with open(self.in_file_path, 'rb') as inp:
            table = [0] * 257
            for bit in range(257):
                byte_str = inp.read(1)
                string = int.from_bytes(byte_str, 'big')
                table[bit] = string
            print(table)
                # break
        tree = Tree()
        tree.generate_code_tree(table)


    def int_from_bytes(self, xbytes):
        return int.from_bytes(xbytes, 'big')

    def load_vocabulary(self, vocabulary_file_path):
        d = {}
        with open(vocabulary_file_path, 'rb') as voc:
            for line in voc.readlines():
                words = re.split('(\W)', line.decode())
                for word in words:
                    d[word] = 0
        voc.close()
        return d


def run():
    encoder = HuffmanEncode("datasheet.txt", "words.txt", "test.txt")
    encoder.compress()

    # decoder = HuffmanDecode("test.txt", "words.txt", "test-decode.txt")
    # decoder.decompress()
    # print(encoder.final_words_dict)
    # possibilities = possible_words("words.txt")
    # counted_words = word_occurances("datasheet.txt", possibilities)
    # remaining_words = remove_unused_words(counted_words)
    

run()