import heapq
def count_frequencies(event_streams):
    lit_freq = [0] * 286
    dist_freq = [0] * 30
    """
    this function counts the appearance frequency of each symbol
    including distance symbols but ignores extra bits as they are raw bits
    """
    for event in event_streams:
        if event[0] == "LiteralEvent":
            lit_freq[event[1]] += 1
        elif event[0] == "MatchEvent":
            lit_freq[event[1]] += 1   # length symbol
            dist_freq[event[3]] += 1  # distance symbol
        elif event[0] == "EndEvent":
            lit_freq[256] += 1
    
    return lit_freq, dist_freq




def build_huffman_lengths(freq, alphabet_size):
    """
    this function builds the huffman tree and assigns the code length for each symbol
    this is achieved by using heapq library to build the tree using a priority queue
    """
    heap = []
    for symbol in range(alphabet_size):
        if freq[symbol] > 0: #if a symbol appears in the alphabet, push it into the priority queue
            heapq.heappush(heap, (freq[symbol], symbol, symbol))
    
    if len(heap) == 0: # return an array of zero if the heap is empty
        return [0] * alphabet_size
    
    if len(heap) == 1: # if heap length is 1, assignt all lengths 0 except the symbol in the heap
        lengths = [0] * alphabet_size
        lengths[heap[0][1]] = 1
        return lengths
    # construct the huffman tree by looping through the queue, popping the first 2 entries
    # then merging them and pushing it back
    while len(heap) > 1: 
        freq1, min_sym1, sym1 = heapq.heappop(heap)
        freq2, min_sym2, sym2 = heapq.heappop(heap)
        merged_min = min(min_sym1, min_sym2)
        heapq.heappush(heap, (freq1 + freq2, merged_min, (sym1, sym2)))
    # when pushing, add the frequency of both original nodes, push the min of both for tiebreak
    # between nodes of same frequencies, and a tuple containing original 2 nodes symbols.
    
    lengths = [0] * alphabet_size
    # this function recursively walks down the tree until it finds an int instead of a tuple
    #which suggests reaching a leaf symbol node. it then assigns the depth of that node as the length
    def assign_lengths(node, depth):
        if isinstance(node, int):
            lengths[node] = depth
        else:
            assign_lengths(node[0], depth + 1)
            assign_lengths(node[1], depth + 1)
    
    assign_lengths(heap[0][2], 0)
    return lengths



#this function takes lengths from the past function to generate the huffman codes
def canonical_huffman(lengths):
    count = [0] * 16 #array index are all the lengths 0-15
    for length in lengths:
        count[length] += 1  #increment by one when finding each length
    
    count[0] = 0 #reset 0 count as it is not used

    #compute the first code of each length by adding the first code of previous length 
    #plus how many symbols had that length, then left shift to move to the next tree level
    next_code = [0] * 16 
    code = 0
    for bits in range(1, 16): 
        code = (code + count[bits - 1]) << 1 
        next_code[bits] = code

    #walk through the symbols in order, assign the next available code for that length
    symbol_code = [None] * len(lengths)
    for symbol in range(len(lengths)):
        length = lengths[symbol]
        if length != 0:
            symbol_code[symbol] = (next_code[length], length)
            next_code[length] += 1 #increment so the next symbol of same length gets the next available code
    
    return symbol_code