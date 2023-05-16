'''Text compression using words.txt file'''
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
            node.left_child = self
            node.right_child = other
            return node

    def is_leaf(self):
        if self.symbol is not None:
            return True
        return False

class Tree(object):
    def __init__(self, collection=None):
        if collection is not None:
            self.heap = self._build_heaps(collection)
            self.top_nodes = self._build_trees()
            self.codes = self._build_code_trees()

    def _build_heaps(self, collections):
        heaps = []
        for arr in collections:
            heaps.append(self._build_heap(arr))
        return heaps

    def _build_heap(self, collection):
        '''building BST from dict'''
        heap = []
        for sym in collection:
            node = Node(sym, 1)
            heapq.heappush(heap, node)
        return heap

    def _build_trees(self):
        trees = []
        for heap in self.heap:
            while(len(heap) > 1):
                left_child, right_child = heapq.heappop(heap), heapq.heappop(heap)
                parent = left_child + right_child
                heapq.heappush(heap, parent)
            #should only be top node left, return it
            trees.append(heapq.heappop(heap))
        return trees
    
    def _build_code_trees(self):
        tree_codes = []
        for tree in self.top_nodes:
            if tree is not None:
                codes = {}
                self._add_codes(tree, '', codes)
            tree_codes.append(codes)
        return tree_codes

    def _add_codes(self, current_node, current_code, codes):
        if current_node is not None:
            if current_node.symbol is not None:
                codes[current_node.symbol] = current_code
            self._add_codes(current_node.left_child, current_code+'0', codes)
            self._add_codes(current_node.right_child, current_code+'1', codes)

class Reader(object):
    def __init__(self, in_file_path="datasheet.txt", vocabulary_file_path='words.txt', output_file_path='output.txt'):
        self.in_file_path = in_file_path
        self.out_file_path = output_file_path
        self.vocabulary_file_path = vocabulary_file_path
        self.collections = self.parse(vocabulary_file_path)

    def parse(self, words):
        '''
        Reads every word into a 2d array storing words by their first letter
        [[a, apa, alfons], [A, APA], [b, bi, bil..]...]
        '''
        #minimum 4? 1 byte for index and then 2 bytes to store code? ex. a101010101010000000000000
        min_len = 4
        with open(words, 'r+') as words_in:
            collection = []
            for line in words_in.readlines():
                add_line = True
                # removing new line \n from every word
                for item in collection:
                    if len(line) > min_len:
                        #putting each word in its own array alphabeticly
                        if line[0] == item[0][0]:
                            item.append(line)
                            add_line = False
                            break
                if add_line and len(line) > min_len:
                    new_arr = [line]
                    collection.append(new_arr)
        return collection

class Encoder(Reader):
    def compress(self):
        '''
        Compresses the file by dividing all words to sub-lists categorized by their first letter.
        If the word is found in words.txt its compressed to an affix pointing to its list followed by its coded value
        e.g. 'v(' which is the encoded value of 'vital' thus saving 2 bytes
        '''
        writer = open(self.out_file_path, 'wb')
        tree = Tree(self.collections)
        # possibly change this to not read bytes and skip decoding
        with open(self.in_file_path, 'rb') as in_text:
            for line in in_text.readlines():
                words = re.split('(\W)', line.decode())
                for word in words:
                    tup = self.get_binary_code(tree, word) #word, code
                    self.write(writer, tup[0], tup[1])
        in_text.close()
        writer.close()

    def get_binary_code(self, tree, word):
        '''Tries to find the coded repr of word else returns word'''
        if len(word) > 0:
            for arrs in tree.codes:
                for key, val in arrs.items():
                    # print('key: {}  word: {}'.format(key, word))
                    if key[0] == word[0]:
                        #we are in the right place, look for the word
                        if key == word+'\n':
                            return (key, val)
                    else:
                        #we are not in the right place, no need to loop here
                        break
        return (word, None)

    def write(self, writer, word, code=None):
        '''writes as bytes to file'''
        if code is not None:
            writer.write(word[0].encode())
            while len(code) > 0:
                writer.write(bytes((int(code[:8], 2), )))
                code = code[8:]
        else:
            writer.write(word.encode())

class Decoder(Reader):
    def decompress(self):
        '''
        Creates table/tree from words file
        Tries to decode word between spaces using table, if its no match word was not encoded.
        Appends word to decoded arr and finally writes the arr to file.
        '''
        tree = Tree(self.collections)
        with open(self.in_file_path, 'rb') as inp:
            tmp = ''
            decoded = []
            new_line = False
            current = inp.read(1)
            while current != b'':
                if current is b' ' or current is b'\n':
                    decoded.append(self.decode(tmp, tree.codes))
                    if new_line:
                        decoded.append(self.decode(f'{13:08b}' + f'{10:08b}', tree.codes)) # coded \r\n
                    tmp = ''
                    new_line = False
                else:
                    if current is not b'\r':
                        tmp += f'{int.from_bytes(current, "big"):08b}'
                    else:
                        new_line = True
                current = inp.read(1)
        self.write(decoded)

    def decode(self, tmp, tree_codes):
        '''
        Tries to find the coded string e.g. '1010101010101001010100101' in the table
        Some ugly fixes in here, lots of special cases that needs to be implemented or re-think how 
        the file is encoded / parsed.
        '''
        try:
            letter = tmp[:8]
            tmp = tmp[8:]
            for codes in tree_codes:
                for key,val in codes.items():
                    # finds the affix of the binary string and decodes it to a letter
                    if key[0] == chr(int(letter, 2)):
                        # print("val: {}      tmp: {}".format(val, tmp))
                        # if val[:8] == tmp[:8]:
                        if val[:len(tmp)-8] == tmp[:len(tmp)-8]:
                            # print("all good this far")
                            for i in range(len(tmp[8:])):
                                if val[8:] == tmp[8+i:]:
                                    # print("found decoded word: ", key)
                                    return key[:len(key)-1]
            # this doesnt seem to be encoded, return the word
            word = letter+tmp
            res = ''
            while len(word) > 0:
                ascii_nbr = int(word[:8], 2)
                char = chr(ascii_nbr)
                special_cases = ['\x80', '\x99', '\x12', '\x01', None, '\x9a', '\x93', '\x19', '\x8c', '\x94'] #quick fix to remove stuff killing the program
                if char not in special_cases:
                    if char == 'â':
                        res += "’"
                    else:
                        res += char
                word = word[8:]
            # print("found not encoded word: ", res)
            return res
        except Exception as err:
            # print("in except", err)
            pass
                            

    def write(self, decoded):
        '''writes provided array to file'''
        with open(self.out_file_path, 'w+') as out:
            for word in decoded:
                if word == '\r\n':
                    out.write(word)
                else:
                    try:
                        out.write(word + ' ')
                    except Exception as err:
                        # print("Couldnt write {} to file, with err: {}".format(word, err))
                        pass


def run():
    '''aka main'''
    encoder = Encoder("datasheet.txt", "words.txt", "encoded-datasheet.txt")
    encoder.compress()

    decoder = Decoder("encoded-datasheet.txt", "words.txt", "decoded-datasheet.txt")
    decoder.decompress()

run()