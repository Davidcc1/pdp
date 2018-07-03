# README #

Implementation of Scalable and Efficient provable data possession.

Actually server and client are in the same git project.

Server: 

command:
	
	python server.py 
	
Client:

Has two basic algorithms diferenced by mode. 

Store mode command is:
	
	python client.py mode=store k=128,t=15,r=16,nB=128 data.txt
	
	- k-> n bits of keis
	- t -> number of tokens (possible challenges) example = 50
	- r -> indices per verification example = 16
	- nB -> number of blocks = 128
	
Challenge mode command is:

	python client.py mode=challenge i=1,f_data=02_02_18-1856,r=16
	
	- i -> token to verification
	- f_data -> file date to validate
	- r -> indices per verification example = 16
	
