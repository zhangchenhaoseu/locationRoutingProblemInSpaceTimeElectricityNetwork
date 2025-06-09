import pandas as pd


def generateStsNode(readPath):
    savePath = r'STE_node.txt'
    readDf = pd.read_csv(readPath)
    # print(readDf)

    file = open(savePath, 'w').close()
    file_generate = open(savePath, mode='a')
    file_generate.write(str('space') + "," + str('time') + ","+ str('electricity'))  
    file_generate.write('\n')

    nodeList = list(pd.unique(readDf['from_node']))
    timeStampList = [i for i in range(0,10)]  # research horizon
    electricityList = [0,1,2,3,4]  # electricity set

    for i in nodeList:
        space = i
        for t in timeStampList:
            time = t
            for e in electricityList:
                electricity = e
                file_generate.write(str(space) + "," +str(time) + ","+str(electricity))
                file_generate.write('\n')

    file_generate.close()


if __name__ == "__main__":
    path = r'link_ini.txt'
    generateStsNode(path)
