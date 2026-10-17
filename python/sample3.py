myset={"Blue","red","green","yellow"}
print(myset)

print(len(myset))

thisset=set(("car","bus","bike"))
print(thisset)

for x in myset:
    print(x)
    
print("banana" in myset)
print("banana" not in myset)

myset.add("orange")
print(myset)

myset.update(thisset)
print(myset)

myset.remove("Blue")
print(myset)

print(thisset)
print(myset)

x=thisset.pop()
print(x)

myset.pop()
print(myset)

thisset.clear()
print(thisset)

