### What is Node Explorer?
===========
Ethernity Cloud node explorer is a script which provides an easy way to find all the nodes which interacted with Ethernity Cloud's smart contract.
The explorer's purpose is to be integrated in various dashboards to get a visual representation about nodes activity.

### Requirements
===========
python >= 3.5 (Find out which version is installed by running "python3 -V")
Web3 module >=4.0 (Find out which is installed by running "pip show web3")

### Ubuntu Instructions
===========
sudo apt install python3 pip -y
pip install web3
git clone https://github.com/ethernity-cloud/etny-node-explorer

### Running
===========
Launch the script with "python3 nodes_reader.py"
The script works by scanning the blockchain for nodes which interacts with the smart contract and saves the output to a CSV file.
The first time the script creates an local index by scanning the blockchain. This takes a *long* time, usually about 5 hours. 
Subsequent runs will run much faster by looking at the differences.

### File Details
===========
*config.env* - Environment config such as blockchain provider, smart contract address, index file and output file
[DEFAULT]
HttpProvider = https://core.bloxberg.org
ContractAddress = 0x549A6E06BB2084100148D50F51CF77a3436C3Ae7
IndexFile = data.json
CSVFile = nodes.csv

*data.json* - Data dictionary with request ids and data processing request containing block number 

*nodes.csv* - Output of the script with the details of the nodes interacting with the smart contract

*nodes.csv column details*
[Column 01] = id
[Column 02] = Wallet address
[Column 03] = CPU Number of Cores
[Column 04] = RAM
[Column 05] = Storage
[Column 06] = Bandwith
[Column 07] = Max Duration of a running task
[Column 08] = Status of a task
[Column 09] = Cost for running a task
[Column 10] = Created on: unix timestamp
[Column 11] = Last updated on: unix timestamp
