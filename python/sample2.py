tuple1=("apple","1","cherry","2")
print(tuple1)

tuple2=tuple(("blue","Red","Green","1"))
print(tuple2)

print(tuple1[1])
print(tuple2[0])

y=list(tuple1)
y[1]="kiwi"
print(y)

x=tuple(y)
print(x)

y=list(x)
print(y)

y.append("orange")
y.remove("kiwi")
print(y)

x=tuple(y)
print(x)

