num=[1,2,3,4,5]
print(num)

num.append(6)
print(num)

del num[2]
print(num)

sum1=sum(num)
print(sum1)





fruit=("apple","Kiwi","orange","mango")
print(fruit)

print(fruit[0])
print(fruit[3])

x=list(fruit)
print(x)





number={1,2,3,4,2,1,4,5,1,2}
print(num)

number.add(8)
print(number)

number.remove(4)
print(number)





person={
    "name":"murshida",
    "age":20,
    "city":"kozhikode"
}
print(person)

person["email"]="murshida@gmail.com"
print(person)

person["age"]=21
print(person)

print("keys:")
for key in person.keys():
    print(key)
