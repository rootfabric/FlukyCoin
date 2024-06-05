"""

Пример дерева Меркле, для синхронизации хранилищ
Работает корректно при сравнении если первое больше второго!

"""

import hashlib
import json

class MerkleTree:
    def __init__(self):
        self.leaves = []
        self.tree = []

    def add_hash(self, data_hash: str):
        self.leaves.append(data_hash)
        self.build_tree()

    def build_tree(self):
        current_level = self.leaves[:]
        self.tree = [current_level]
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined_hash = hashlib.sha256((current_level[i] + current_level[i + 1]).encode()).hexdigest()
                else:
                    combined_hash = current_level[i]
                next_level.append(combined_hash)
            current_level = next_level
            self.tree.append(current_level)

    def get_level_hashes(self, level):
        if level < len(self.tree):
            return self.tree[level]
        return []

    def get_count_levels(self):
        return len(self.tree)

class DistributedStorage:
    def __init__(self):
        self.merkle_tree = MerkleTree()

    def add_hash(self, data):
        hash_value = hashlib.sha256(data.encode()).hexdigest()
        self.merkle_tree.add_hash(hash_value)

    def serialize_levels(self, levels):
        data = {"levels": {level: self.merkle_tree.get_level_hashes(level) for level in levels}}
        return json.dumps(data)

    @staticmethod
    def deserialize_levels(data):
        data = json.loads(data)
        storage = DistributedStorage()
        max_level = max(map(int, data["levels"].keys()))
        storage.merkle_tree.tree = [[] for _ in range(max_level + 1)]
        for level, hashes in data["levels"].items():
            if hashes:
                storage.merkle_tree.tree[int(level)] = hashes
        return storage

    def compare_levels(self, other_storage):
        max_level = max(len(self.merkle_tree.tree), len(other_storage.merkle_tree.tree))
        differences = {}
        for level in range(max_level):
            own_hashes = self.merkle_tree.get_level_hashes(level)
            other_hashes = other_storage.merkle_tree.get_level_hashes(level)
            missing = list(set(own_hashes) - set(other_hashes))
            extra = list(set(other_hashes) - set(own_hashes))
            if missing or extra:
                differences[level] = {'missing': missing, 'extra': extra}
        return differences

    def analyze_detailed_differences(self, level_differences, level):
        missing_hashes = level_differences.get('missing', [])
        extra_hashes = level_differences.get('extra', [])
        detailed_missing = set()
        detailed_extra = set()

        for hash in missing_hashes:
            detailed_missing.update(self.get_leaf_descendants(hash, level))

        for hash in extra_hashes:
            detailed_extra.update(self.get_leaf_descendants(hash, level))

        return {'missing_hashes': list(detailed_missing), 'extra_hashes': list(detailed_extra)}

    def get_leaf_descendants(self, hash, level):
        if level == 0:
            return [hash]
        descendant_hashes = []
        child_hashes = self.request_child_hashes(hash, level)
        if child_hashes:
            for child_hash in child_hashes:
                descendant_hashes.extend(self.get_leaf_descendants(child_hash, level - 1))
        else:
            descendant_hashes.append(hash)
        return descendant_hashes

    def request_child_hashes(self, parent_hash, level):
        if level > 0 and parent_hash in self.merkle_tree.tree[level]:
            parent_index = self.merkle_tree.tree[level].index(parent_hash)
            child_start_index = parent_index * 2
            children = []
            if child_start_index < len(self.merkle_tree.tree[level - 1]):
                children.append(self.merkle_tree.tree[level - 1][child_start_index])
            if child_start_index + 1 < len(self.merkle_tree.tree[level - 1]):
                children.append(self.merkle_tree.tree[level - 1][child_start_index + 1])
            return children
        return []

# Пример использования
storage1 = DistributedStorage()
storage2 = DistributedStorage()


for i in range(200):
    storage1.add_hash(f"transaction_{i}")
for i in range(190):
    storage2.add_hash(f"transaction_{i}")

max_layer = storage1.merkle_tree.get_count_levels()
print("get_count_levels", storage1.merkle_tree.get_count_levels())
level = min(max_layer-1, 2)


serialized_levels = storage1.serialize_levels([level])
print(len(serialized_levels), serialized_levels)
restored_storage = DistributedStorage.deserialize_levels(serialized_levels)
differences = restored_storage.compare_levels(storage2)

print(f"Differences at level {level}:", differences.get(level, {}))

detailed_diffs = storage1.analyze_detailed_differences(differences.get(level, {}), level)
print("Detailed Missing Hashes:", len(detailed_diffs['missing_hashes']), detailed_diffs['missing_hashes'])
print("Detailed Extra Hashes:", detailed_diffs['extra_hashes'])

def find_missing_hashes(first_list, second_list):
    missing_hashes = [hash for hash in first_list if hash not in second_list]
    return missing_hashes

missing_hashes = find_missing_hashes(storage1.merkle_tree.leaves, storage2.merkle_tree.leaves)
print("Missing really hashes in second list:", len(missing_hashes),  missing_hashes)

print("storage1.merkle_tree.leaves", storage1.merkle_tree.leaves)
print("storage2.merkle_tree.leaves", storage2.merkle_tree.leaves)
