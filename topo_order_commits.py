
# Keep the function signature,
# but replace its body with your implementation.
#
# Note that this is the driver function.
# Please write a well-structured implemention by creating other functions outside of this one,
# each of which has a designated purpose.
#
# As a good programming practice,
# please do not use any script-level variables that are modifiable.
# This is because those variables live on forever once the script is imported,
# and the changes to them will persist across different invocations of the imported functions.

#!/usr/bin/env python3

# Recommended libraries. Not all of them may be needed.
import copy, os, sys, re, zlib
from collections import deque

# Note: This is the class for a doubly linked list. Some implementations of
# this assignment only require the `self.parents` field. Delete the
# `self.children` field if you don't think its necessary.
class CommitNode:
    def __init__(self, commit_hash):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()
    def add_parent(self, parent_commit):
        self.parents.add(parent_commit)
    def add_child(self, child_commit):
        self.children.add(child_commit)
    def __repr__(self):
        return (f"parents={list(self.parents)}")
                #f"children={list(self.children)})")

# ============================================================================
# ======================== Auxiliary Functions ===============================
# ============================================================================

def in_git_directory() -> bool:
    """
    :rtype: bool

    Checks if `topo_order_commits.py` is inside a Git repository.
    """
    return os.path.exists(".git")


def get_branch_hash(branch_name : str) -> str:
    """
    :type branch_name: str
    :rtype: str

    Returns the commit hash of the head of a branch.
    """
    with open(branch_name, "r") as f:
        head = f.read().strip()
        return head

def decompress_git_object(commit_hash : str) -> list[str]:
    """
    :type commit_hash: str
    :rtype: list

    Decompresses the contents of a git object and returns a
    list of the decompressed contents.
    """
    file_path = os.path.join(".git", "objects", commit_hash[:2], commit_hash[2:])
    #print(f"Attempting to open file: {file_path}")
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        contents = zlib.decompress(data).decode()
        return contents.split('\n')
    except FileNotFoundError as e:
        #print(f"File not found: {file_path}")
        return None
    
    

# ============================================================================
# =================== Part 1: Discover the .git directory ====================
# ============================================================================

def get_git_directory() -> str:
    """
    :rtype: str
    Returns absolute path of `.git` directory. os.getcwd() os.path.exists() os.path.dirname() parent dir 
    """
    current_dir = os.getcwd()
    #interate up to parent until dir contains git repo
    while current_dir != '/':
        if os.path.exists(os.path.join(current_dir, ".git")):
            return os.path.join(current_dir, ".git")
        current_dir = os.path.dirname(current_dir)
    #if root reached output err
    sys.stderr.write("Not inside a Git repository\n")
    sys.exit(1)

# ============================================================================ 
# =================== Part 2: Get the list of local branch names =============
# ============================================================================

def get_branches(path : str) -> list[(str, str)]:
    """
    :type path: str
    :rtype: list[(str, str)]

    Returns a list of tupes of branch names and the commit hash
    of the head of the branch.
    """
    branches = []
    refs_path = os.path.join(path, 'refs', 'heads')
    for root, _, files in os.walk(refs_path):
        for file in files:
            branch_path = os.path.join(root, file)
            branch_name = os.path.relpath(branch_path, refs_path)
            commit_hash = get_branch_hash(branch_path)
            branches.append((branch_name, commit_hash))
    return branches

# ============================================================================
# =================== Part 3: Build the commit graph =========================
# ============================================================================

def build_commit_graph(branches_list : list[(str, str)]) -> \
    dict[str, CommitNode]:
    """
    :type branches_list: list[(str, str)]
    :rtype: dict[str, CommitNode]
    """
    commit_graph = {}
    visited = set()
    #get branch heads as list of hashes to process
    hashes_to_process = [branch_head for _, branch_head in branches_list]
    #print("hashes_to_process: ", hashes_to_process)
    while hashes_to_process:
        #pick hash remove from proc list
        curr_hash = hashes_to_process.pop()
        #if visited before skip proc
        if curr_hash in visited:
            continue
        #if hash not in graph make node and store it
        visited.add(curr_hash)

        if curr_hash not in commit_graph:
            commit_graph[curr_hash] = CommitNode(curr_hash)
        #retrieve node from graph
        curr_node = commit_graph[curr_hash]
        #print("curr_node: ", curr_node, curr_hash)
        contents = decompress_git_object(curr_hash)
        if contents is None:
            continue
        contents_str = '\n'.join(contents)
        #retrieve parents from commit fit
        parent_hashes = re.findall(r'parent ([0-9a-f]+)', contents_str)

        for parent_hash in parent_hashes:
            if parent_hash not in visited:
                hashes_to_process.append(parent_hash)
            if parent_hash not in commit_graph:
                commit_graph[parent_hash] = CommitNode(parent_hash)
                #print("parent", parent_hash, commit_graph[parent_hash])
            
            commit_graph[parent_hash].add_child(curr_hash)
            curr_node.add_parent(parent_hash)

    #print("commit_graph: ")
    #for commit_hash, node in commit_graph.items():
        #print(f"{commit_hash}: {node}")
    return commit_graph

# ============================================================================
# ========= Part 4: Generate a topological ordering of the commits ===========
# ============================================================================

def topo_sort(commit_nodes : dict[str, CommitNode]) -> list[str]:
    """
    :type commit_nodes: dict[str, CommitNode]
    :rtype: list[str]

    Generates a topological ordering of the commits in the commit graph.
    The topological ordering is represented as a list of commit hashes. See
    the LA Worksheet for some starter code for Khan's algorithm.
    """
    #init indegree dict, all nodes 0
    indegree = {commit_hash: 0 for commit_hash in commit_nodes}

    #calc num parents/indegree for each commit node
    for commit_hash, node in commit_nodes.items():
        for parent_hash in node.parents:
            indegree[parent_hash] += 1

    #init deque w nodes
    q = deque(commit_hash for commit_hash, degree in indegree.items() if degree == 0)
    result = []

    while q:
        commit_hash = q.popleft()
        result.append(commit_hash)
        #print("append_res: ", result)
        #update indegree
        for parent_hash in commit_nodes[commit_hash].parents:
            indegree[parent_hash] -= 1
            if indegree[parent_hash] == 0:
                q.append(parent_hash)

    if len(result) != len(commit_nodes):
        print("Cycle")
        return []
    #print("result: ", result)
    return result

# ============================================================================
# ===================== Part 5: Print the commit hashes ======================
# ============================================================================
def ordered_print(
    commit_nodes: dict[str, CommitNode],
    topo_ordered_commits: list[str],
    head_to_branches: dict[str, list[str]]
):
    printed_commits = set()
    jump = False
    for i, commit in enumerate(topo_ordered_commits):
        curr_node = commit_nodes[commit]

        if commit in printed_commits:
            continue  # Skip printing duplicate commits

        if jump: #empty line just printed
            child_hashes = curr_node.children
            jump = False
            #print children starting with =
            print("=", end="") #no whitespace after equal sign
            if child_hashes:
                for child in child_hashes:
                    print(child)
        print(commit, end="")

        #print branches
        if commit in head_to_branches:
            branches = sorted(head_to_branches[commit])
            print(" " + " ".join(branches), end="")
        print()

        printed_commits.add(commit)  # Add commit to printed set

        # Check if there is a next commit
        has_next_commit = i + 1 < len(topo_ordered_commits)
        if (i+1 == len(topo_ordered_commits)):
            return

        # Get the next commit hash if it exists
        if has_next_commit:
            next_commit_hash = topo_ordered_commits[i + 1]
        else:
            next_commit_hash = None
        
        parent_hashes = curr_node.parents
        if next_commit_hash not in parent_hashes:
            jump = True
            #print parents of curr commit followed by =
            
            if parent_hashes:
                for parent in parent_hashes:
                    print(parent, end=" ") #parent hashes sep by whitespace
            print()
            print("=") #if no parents just =
            print() #NL after end=

def ordered_print2(
    commit_nodes : dict[str, CommitNode],
    topo_ordered_commits : list[str],
    head_to_branches : dict[str, list[str]]
):
    """
    :type commit_nodes: dict[str, CommitNode]
    :type topo_ordered_commits: list[str]
    :type head_to_branches: dict[str, list[str]]

    Prints the commit hashes in the the topological order from the last
    step. Also, handles sticky ends and printing the corresponding branch
    names with each commit.
    """
    def print_sticky_start(commit_hash: str, printed_commits: list[str]):
        """
        Prints the sticky start for the given commit hash. sticky start
        """
        children_hashes = commit_nodes[commit_hash].children
        print(f"={commit_hash}", end="")
        if children_hashes:
            print(" " + " ".join(children_hashes), end="") #any order sep by whitespace
            for i in children_hashes:
                printed_commits.add(i)
        print()

    #insert sticky end - commit hash of parents of curr, = to last hash
    def print_sticky_end(parent_hashes: list[str], printed_commits: list[str]):
        """
        Prints the sticky end for the given parent hashes.
        """
        print("=", end="") #if no parents just =
        if parent_hashes:
            print(" " + " ".join(parent_hashes), end="")
            for i in parent_hashes:
                printed_commits.add(i)
        print()

    #if next commit not parent of curr insert sticky end
    
    #if empty line j printed print sticky start =
    #commit corresp to branch head or heads branch names listed after commit in 

    # empty set to keep track of printed commits
    printed_commits = set()
    newSegment = False
    for i, commit_hash in enumerate(topo_ordered_commits):
        # if commit_hash not in printed_commits:
        #     print_sticky_start(commit_hash, printed_commits)

        # Determine if a sticky start should be printed
        if newSegment:
            print_sticky_start(commit_hash, printed_commits)
            newSegment = False

        # Print commit hash
        print(commit_hash, end="")

        # Print associated branch names
        if commit_hash in head_to_branches:
            branches = sorted(head_to_branches[commit_hash])
            print(" " + " ".join(branches), end="")
        print()

        printed_commits.add(commit_hash)

        #parent_hashes = commit_nodes[commit_hash].parents

        # Determine if a sticky end should be printed
        next_commit_hash = topo_ordered_commits[i + 1] if i + 1 < len(topo_ordered_commits) else None

        # if not next_commit_is_parent or i == len(topo_ordered_commits) - 1:
        #     print_sticky_end(list(parent_hashes))
         # If the next commit is not a parent of the current commit, print sticky end
        if next_commit_hash and next_commit_hash not in commit_nodes[commit_hash].parents:
            print_sticky_end(list(commit_nodes[commit_hash].parents), printed_commits)
            print()
            newSegment = True

    # # iterate thru topo_ordered_commits list
    # for commit_hash in topo_ordered_commits:
    #     # print sticky start if commit hash has not been printed yet
    #     if commit_hash not in printed_commits:
    #         print_sticky_start(commit_hash)

    #     # print commit hash
    #     print(commit_hash, end=" ")

    #     # print associated branch names
    #     if commit_hash in head_to_branches:
    #         #sorted is deterministic
    #         branches = sorted(head_to_branches[commit_hash])
    #         print(" ".join(branches), end=" ")

    #     # mark commit as printed
    #     printed_commits.add(commit_hash)

    #     # get parent hashes of the current commit
    #     parent_hashes = commit_nodes[commit_hash].parents

    #     # print sticky end if there are parent hashes
    #     if parent_hashes:
    #         print_sticky_end(parent_hashes)
    #     else:
    #         print("=")

# ============================================================================
# ==================== Topologically Order Commits ===========================
# ============================================================================

def topo_order_commits():
    """
    Combines everything together.
    """
    # Check if you are inside a Git repository.
    
    # Part 1: Discover the .git directory.
    #print("part1")
    gdir = get_git_directory()
    # Part 2: Get the list of local branch names.
    #print("part2")
    branch_names = get_branches(gdir)
    # Part 3: Build the commit graph
    #print("part3")
    commit_graph = build_commit_graph(branch_names) #ERROR
    # Part 4: Generate a topological ordering of the commits in the graph.
    #print("part4")
    topo_order_list = topo_sort(commit_graph)
    # Generate the head_to_branches dictionary showing which
    # branches correspond to each head commit
    #print("topo_order_list: ", topo_order_list)
    
    #print("part5")
    head_to_branches = {}
    for branch, head_commit in branch_names:
        if head_commit not in head_to_branches:
            head_to_branches[head_commit] = []
        head_to_branches[head_commit].append(branch)

    # Part 5: Print the commit hashes in the topological order.
    #print("part6")
    ordered_print(commit_graph, topo_order_list, head_to_branches)

# ============================================================================

if __name__ == '__main__':
    topo_order_commits()
