
import webcam as wb
print("----------------------------FACE ATTENDANCE SYSTEM-----------------------")
print("Enter Your choices")
print("a) Add Data to Database")
print("b) Delete Data")
print("c) Update Data")
print("d) Start Class")
print("e) Exit")

while True:
    a=input("Enter Your choice")
    if a=='a':
        wb.addDetails()
    elif a=='b':
        k=input("Enter key to be deleted: ")
        wb.delete(k)
    elif a=='c':
        k = input("Enter Id to be updated: ")
        wb.update(k)

    elif a=='d':
        wb.webC()
    elif a=='e':
        exit(0)
    else:
        print ("wrong choice")