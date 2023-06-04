a = 1;
format shortg
c = clock
c = c(4)* 60 * 60 + c(5)* 60 + c(6)

h = [2 3 4 5 6 64 4 5]

c = [8.99]

timestamp = [c h]

timestamp2 = timestamp + 1

all = timestamp
all = [timestamp; timestamp2]
all = [all; timestamp]

emg = all 

cursor = [1 1]

tb = table(cursor,emg) ;
Mdl = fitrnet(X,Y) 
Mdl = fitrsvm(tb,'y','KernelFunction','gaussian');
YFit = predict(Mdl,tb);
