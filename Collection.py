import os
import json
from enum import Enum
from typing import Any, Union, List
from DataNode import DataNode


class Collection:
    __dirname: str = ""
    __collectionName: Union[str, None] = None
    __root: Any = None
    __schema: Any = None

    def __init__(self, collectionName, baseRoot: str, generate=False):
        dirname = os.path.join(baseRoot, collectionName)
        self.__dirname = dirname
        if generate:
            try:
                if not os.path.exists(dirname):
                    os.makedirs(dirname)
                    self.__collectionName = collectionName
                else:
                    print("Error : Already Exists collection")
            except OSError:
                print("Error : Creating collection. " + collectionName)
        else:
            if os.path.exists(dirname):
                self.__collectionName = collectionName
                self.__load()
            else:
                print("Error : Not Exists collection")

    def __str__(self):
        return self.__collectionName

    def __load(self):
        filelist = os.listdir(self.__dirname)
        for file in filelist:
            if file[-5:] == ".json":
                if file[:6] == ".schema":
                    with open(
                        os.path.join(self.__dirname, file), "r", encoding="UTF8"
                    ) as jsonfile:
                        self.__schema = DataNode(
                            json.load(jsonfile), "schema", self.__dirname
                        )
                else:
                    with open(
                        os.path.join(self.__dirname, file), "r", encoding="UTF8"
                    ) as jsonfile:
                        data = json.load(jsonfile)
                        self.insert(data, file[:-5])

    def __rotate(self, direction: str, rotateRoot: DataNode):
        parent = rotateRoot.parent
        if direction.lower() == "left":
            newRoot = rotateRoot.right
            if newRoot == None:
                return False
            rotateRoot.right = newRoot.left
            newRoot.left = rotateRoot
            if rotateRoot.right != None:
                rotateRoot.right.parent = rotateRoot
        elif direction.lower() == "right":
            newRoot = rotateRoot.left
            if newRoot == None:
                return False
            rotateRoot.left = newRoot.right
            newRoot.right = rotateRoot
            if rotateRoot.left != None:
                rotateRoot.left.parent = rotateRoot
        else:
            return
        rotateRoot.parent = newRoot
        if rotateRoot == self.__root:
            self.__root = newRoot
            # newRoot.parent = None
        elif parent.left == rotateRoot:
            parent.left = newRoot
        elif parent.right == rotateRoot:
            parent.right = newRoot
        newRoot.parent = parent
        self.updateHeight(rotateRoot)
        return True

    def __rebalance(self, root: DataNode):
        while root != None:
            balance = root.getBalance()
            p = root.parent
            sub = None
            if balance > 1:
                sub = root.left
                if sub.getBalance() < 0:
                    self.__rotate("LEFT", sub)
                self.__rotate("RIGHT", root)
            elif balance < -1:
                sub = root.right
                if sub.getBalance() > 0:
                    self.__rotate("RIGHT", sub)
                self.__rotate("LEFT", root)
            self.updateHeight(sub)
            root = p

    def updateHeight(self, node: DataNode):
        while node != None:
            node.updateHeight()
            node = node.parent

    def insert(self, data: dict, dataID: str) -> Union[DataNode, None]:
        if self.__collectionName == None:
            print("Error : NULL collection")
            return None
        if self.__schema != None:
            data2 = self.__schema.getData()
            data2.update(data)
            data = data2
        node = DataNode(data, dataID, self.__dirname)
        if self.__root == None:
            self.__root = node
            return node
        instance = self.__root
        while True:
            if instance.__str__() == dataID and instance.__str__() != None:
                print("exests Node")
                return None
            elif instance.__str__() > dataID:
                if instance.left == None:
                    instance.left = node
                    node.parent = instance
                    break
                else:
                    instance = instance.left
            else:
                if instance.right == None:
                    instance.right = node
                    node.parent = instance
                    break
                else:
                    instance = instance.right
        self.updateHeight(node)
        self.__rebalance(instance.parent)
        return node

    def delete(self, data: Union[str, DataNode, None]) -> str:
        if self.__collectionName == None:
            print("Error : NULL collection")
            return "Error : Null collection"
        elif data == None:
            return "Error : Null Data"
        dataID: str = str(data)
        try:
            os.remove(os.path.join(self.__dirname, dataID+".json") )
        except OSError:
            return "Error : remove File : " + dataID
        if not isinstance(data, DataNode):
            data = self.getNode(dataID)
        while data.left != None and data.right != None:
            if data.left != None:
                self.__rotate("RIGHT", data)
            elif data.right != None:
                self.__rotate("LEFT", data)
        parent = data.parent
        if self.__root == data:
            self.__root = None
        elif parent.left == data:
            parent.left = None
        else:
            parent.right = None
        del data
        self.__rebalance(parent.parent)
        return "success"

    def getSchema(self) -> Union[DataNode, None]:
        return self.__schema

    def getRoot(self) -> Union[DataNode, None]:
        return self.__root

    def getNode(self, dataID: str) -> Union[DataNode, None]:
        if self.__root == None:
            return None
        node: DataNode = self.__root
        while True:
            if node == None:
                return None
            elif node.__str__() == dataID:
                return node
            elif node.__str__() > dataID:
                node = node.left
            else:
                node = node.right
        return None

    # use dfs Search

    def getNames(self) -> List[str]:
        stack: List[DataNode] = []
        names: List[str] = []
        node = self.__root
        isPop = False
        while not isPop or len(stack) != 0:
            if isPop:
                node = stack.pop()
                names.append(node.__str__())
                if node.right != None and node.right.__str__() not in names:
                    node = node.right
                    isPop = False
            else:
                stack.append(node)
                if node.left == None:
                    isPop = True
                else:
                    node = node.left
        return names

    def getAll(self) -> List[DataNode]:
        stack: List[DataNode] = []
        result: List[DataNode] = []
        node = self.__root
        isPop = False
        while not isPop or len(stack) != 0:
            if isPop:
                node = stack.pop()
                result.append(node)
                if node.right != None and node.right not in result:
                    node = node.right
                    isPop = False
            else:
                stack.append(node)
                if node.left != None:
                    isPop = True
                node = node.left
        return result

    def drop(self):
        if self.__collectionName == None:
            print("Error : NULL collection")
            return
        try:
            for filename in os.listdir(self.__dirname):
                os.remove(os.path.join(self.__dirname, filename + ".json"))
            os.rmdir(self.__dirname)
        except OSError:
            print("Error failed to remove folder ", self.__dirname)
            return
