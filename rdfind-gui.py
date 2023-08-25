import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo
import os
import sys

totalRemoved = 0

def createTree(root):
    # define columns
    columns = ('file', 'copies', 'size')

    # create a treeview
    #tree = ttk.Treeview(root, columns=columns, show='headings')
    tree = ttk.Treeview(root, columns=columns, show='tree headings')
    #tree.heading('#0', text='Departments', anchor=tk.W)

    tree.column('#0', width=20, stretch=False)
    tree.column('file', width=100, stretch=True) #, anchor=tk.W
    tree.column('copies', width=100, stretch=False)
    tree.column('size', width=200, stretch=False) #anchor=tk.CENTER

    # define headings
    tree.heading('#0', text='')
    tree.heading('file', text='File Name') # , anchor=tk.W
    tree.heading('copies', text='Copies')
    tree.heading('size', text='Size')

    # place the Treeview widget on the root window
    tree.grid(row=0, column=0, sticky=tk.NSEW)

    scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky='ns')

    tree.bind("<Double-1>", OnDoubleClickTree)

    return tree

def createList(root):
    # define columns
    columns = ('file', 'size')

    # create a treeview
    #tree = ttk.Treeview(root, columns=columns, show='headings')
    list = ttk.Treeview(root, columns=columns, show='headings')
    #tree.heading('#0', text='Departments', anchor=tk.W)

    list.column('file', width=100, stretch=True) #, anchor=tk.W
    list.column('size', width=200, stretch=False) #anchor=tk.CENTER

    # define headings
    list.heading('file', text='File Name') # , anchor=tk.W
    list.heading('size', text='Size')

    # place the Treeview widget on the root window
    list.grid(row=1, column=0, sticky=tk.NSEW)

    scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=list.yview)
    list.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=1, column=1, sticky='ns')

    return list

def getFileNameFromLine(line):
    words = line.split(' ')
    file = " ".join(words[7:])
    return file

def getSizeFromLine(line):
    words = line.split(' ')    
    return int(words[3])

def parseFile(resultsFileName):
    #rf = open("projects/results.txt")
    rf = open(resultsFileName)
    
    duplications = []
    duplication = None

    while(True):
        line = rf.readline()
        if not line:
            break

        line=line.removesuffix('\n');

        if line.startswith("DUPTYPE_FIRST_OCCURRENCE"):
            file = getFileNameFromLine(line)
            #size = os.stat(file).st_size
            size = getSizeFromLine(line)
            duplication = {'file': file, 'size' : size, 'dups' : []}
            duplications.append(duplication)
        
        elif line.startswith("DUPTYPE_WITHIN_SAME_TREE"):
            file = getFileNameFromLine(line)
            duplication['dups'].append(file)

        else:
            print("ERROR: unsupported line ", line)

    rf.close()
    duplications.sort(key=lambda d: d['size'] * len(d['dups']))
    return duplications

def sizeToText(size):
    gb = size / (1024*1024*1024)
    mb = size / (1024*1024)
    kb = size / (1024)
    if gb > 1:
        return "{:0.2f} GB".format(gb)
    if mb > 1:
        return "{:0.2f} MB".format(mb)
    if kb > 1:
        return "{:0.2f} KB".format(kb)
    return size

def checkChildern(item):
    global totalRemoved
    dups = item['dups']
    removed = False
    for index in range(len(dups) - 1, -1, -1):
        if not os.path.exists(dups[index]):
            del dups[index]
            removed = True
            totalRemoved += 1

    return removed
    
def removeNonExisting(duplications):
    global totalRemoved
    # go over last 100 'duplications'. 
    # - check if children still exist. if they don't - remove them
    # - a parent with no children is also deleted
    # - if at least one file was not found, go over next 100
    print("removing non-existing... ")
    minIndex = len(duplications)
    removed = True
    while removed:
        print("(iteration from ", minIndex)
        minIndex -= 200
        removed = False
        for index in range(minIndex + 200 - 1, max(minIndex, 0), -1):
            item = duplications[index]
            children = item['dups']
            if checkChildern(item):
                removed = True
            if len(children) == 0:
                del duplications[index]                
            elif not os.path.exists(item['file']):
                removed = True
                totalRemoved += 1
                if len(children) <= 1:
                    del duplications[index]
                else:
                    item['file'] = children[0]
                    del children[0]



    print("removed ",totalRemoved," entries")

def insertData(resultsFileName, tree):
    print("parsing file {0}...".format(resultsFileName))
    duplications = parseFile(resultsFileName)
    print("Found ", len(duplications), " unique files")

    removeNonExisting(duplications)    

    for d in duplications:
        size = d['size']
        count = len(d['dups'])
        iid = tree.insert('', tk.END, values=(d['file'], count, sizeToText(size*count)), open=False)
        for c in d['dups']:
            tree.insert(iid, tk.END, values=('   ' +c, 1, sizeToText(size)), open=False)

def OnDoubleClickTree(event):
    item = tree.selection()[0]
    v = tree.item(item,option="values")    
    if not v[0].startswith('   '):
        isOpen = tree.item(item,option="open")
        if not isOpen:
            return
        
        childs = tree.get_children(item)
        if len(childs) == 0:
            print("cannot delete parent with no children")
            return
        
        vc = tree.item(childs[0],option="values")        
        tree.item(item,values=(vc[0].removeprefix('   '), v[1], v[2]))
        tree.delete(childs[0])
    else:
        tree.delete(item)

    newv=(v[0].removeprefix('   '), v[2])
    # check if file exists. if not -  don't insert it...
    if os.path.exists(newv[0]):
        list.insert('', tk.END, values=newv)
    else:
        print("file '", newv[0], "' doesn't exist")

def deleteFiles():
    print("deleting...")
    for item in list.get_children():
        file = list.item(item,option="values")[0]
        print(file)
        os.remove(file)

if len(sys.argv) > 1:
    resultsFileName = sys.argv[1]
else:
    resultsFileName = os.path.join(os.getcwd(),"results.txt" )
root = tk.Tk()

# create root window
root.title('rdfind - GUI')
root.geometry('900x500')

# configure the grid layout
root.rowconfigure(0, weight=2)
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=0, pad=10)
root.columnconfigure(0, weight=1)

tree = createTree(root)

# ttk.Separator(root, orient='horizontal')

list = createList(root)

button = ttk.Button(root, text ="Delete!", command = deleteFiles)
button.grid(row=2, column=0)

insertData(resultsFileName, tree)

# run the app
root.mainloop()