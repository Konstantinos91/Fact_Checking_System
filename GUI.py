import tkinter as tk
import tkinter.messagebox as msgbox
import feature_extraction
import fact_mapping
import fact_response

SUCCESSES = []
FAILURES = []
SEARCHLABELS = []
recentSearchCtr = None
searchResult = None
claim = None
container = None

# set the main container window
def setContainer():
    global container
    container=tk.Tk()
    container.title("F&cTFinder")
    container.geometry("800x500")
    # Add widgets to the container
    addWidgets(container)

    on_load()
    UpdateRecentSearchList()

    container.protocol("WM_DELETE_WINDOW", on_closing)
    container.mainloop()


def on_load():
    global SUCCESSES, FAILURES
    try:
        with open("history.txt", "rt") as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split("|")
                if len(parts) != 2:
                    continue
                if parts[1] == "0":
                    SUCCESSES += [parts[0]]
                else:
                    FAILURES += [parts[0]]
    except:
        pass


def on_closing():
    global container
    with open("history.txt", "wt") as f:
        for succ in SUCCESSES:
            f.write(succ + "|" + "0\n")
        for fail in FAILURES:
            f.write(fail + "|" + "1\n")
    container.destroy()


def addWidgets(con):
    global searchResult, recentSearchCtr, claim
    # Main Window Title
    titleText=tk.Label(con,text="F&cT Finder", font="verdana 24 bold")
    titleText.grid(row=1,column=0,columnspan=3)

    # --------------------------------search widgets-------------------------------
    claimFrame=tk.Frame(con)
    claimFrame.grid(row=2,column=0,columnspan=3)

    claimLabel = tk.Label(claimFrame, text="Enter Claim")
    claimLabel.grid(row=2, column=0)

    claim = tk.StringVar()
    claimBox = tk.Entry(claimFrame, textvariable=claim,exportselection=0,width=100)
    claimBox.grid(row=2, column=1)

    searchBtn=tk.Button(claimFrame,text="Search",command=lambda :Search(claim.get()))
    searchBtn.grid(row=2,column=2)

    #--------------------------------Search Result Container--------------------------
    displayContainer=tk.Frame(con)
    displayContainer.grid(row=3,column=0,columnspan=3)

    searchContainer=tk.LabelFrame(displayContainer,text="Search Result")
    searchContainer.grid(row=3,column=0,sticky="EW",columnspan=3)

    searchResult=tk.Label(searchContainer,text=" ")
    searchResult.grid(row=3,column=0,columnspan=3)

    #-----------------------------------Recent Search Container------------------------

    recentSrchContainer = tk.LabelFrame(displayContainer, text="Recent Searches ")
    #recentSrchContainer.grid(row=4, column=0,padx=10,pady=10,ipadx=10,ipady=10,sticky="ew")
    recentSrchContainer.grid(row=4, column=0, sticky="ew", columnspan=3)
    recentSearchCtr = recentSrchContainer

    #recentSearches = tk.Label(recentSrchContainer, text="This is recent searches searches searches searches  ")
    #recentSearches.grid(row=4, column=0, columnspan=3)

# -------------------------------function called by click event of search button------------
def Search(c):
    global SUCCESSES, FAILURES
    features = feature_extraction.extract(c)

    if features == "failed":
        msgbox.showerror("Error", "Failed to extract features from claim, please check your spelling")
    else:
        facts = fact_mapping.map_facts(features)

        if len(facts) == 0:
            msgbox.showerror("Error", "Your claim doesn't appear to mention any known entity (for example, film or person). Please try again")
        else:
            topfacts = fact_response.rank_facts(facts, features)

            result = fact_response.generate_response(topfacts, features)
            
            if (len(result) == 1 and result[0][0] == True) or (len(result) == 2 and (result[1][0] == True or result[0][0] == True)):
                if not c in SUCCESSES:
                    SUCCESSES += [c]
                    SUCCESSES = SUCCESSES[-5:]
            else:
                if not c in FAILURES:
                    FAILURES += [c]
                    FAILURES = FAILURES[-5:]

            if len(result) == 0:
                searchResult.config(text="False: No facts were found that match the claim")
            elif len(result) == 1:
                searchResult.config(text="True: " + result[0][2])
            elif len(result) == 2:
                if result[0][2] != result[1][2]:
                    searchResult.config(text="True:\nFact 1: " + result[0][2] + "\nFact 2: " + result[1][2])
                else:
                    searchResult.config(text="True: " + result[0][2])
            
    UpdateRecentSearchList() # update the recent search table after each search


def UpdateRecentSearchList():
    global SUCCESSES, SEARCHLABELS, FAILURES, claimBox
    for l in SEARCHLABELS:
        l.destroy()
    SEARCHLABELS = []

    i = 0
    for success in SUCCESSES:
        lbl = tk.Label(recentSearchCtr, text=success, cursor="hand1")
        lbl.grid(row=i, column=0, columnspan=3)
        lbl.bind("<Button-1>", lambda e, s=success: claim.set(s))
        lbl.configure(fg="DarkGreen")
        SEARCHLABELS += [lbl]
        i+=1

    for failure in FAILURES:
        lbl = tk.Label(recentSearchCtr, text=failure, cursor="hand1")
        lbl.grid(row=i, column=0, columnspan=3)
        lbl.bind("<Button-1>", lambda e, s=failure: claim.set(s))
        lbl.configure(fg="DarkRED")
        SEARCHLABELS += [lbl]
        i+=1

#----------------------initiate the call

if __name__ == '__main__':
    setContainer()
