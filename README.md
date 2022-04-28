### What is Node Explorer?
Ethernity Cloud node explorer is a script which provides an easy way to find all the nodes which interacted with Ethernity Cloud's smart contract. <br />
The explorer's purpose is to be integrated in various dashboards to get a visual representation about nodes activity. <br />

### Requirements
python >= 3.5 (Find out which version is installed by running "python3 -V") <br />
Web3 module >=4.0 (Find out which is installed by running "pip show web3") <br />

### Ubuntu Instructions
sudo apt install python3 pip -y <br />
pip install web3 <br />
git clone https://github.com/ethernity-cloud/etny-node-explorer <br />

### Running
Launch the script with "python3 nodes_reader.py".  <br />
The script works by scanning the blockchain for nodes which interacts with the smart contract and saves the output to a CSV file. <br />
When ran for the first time the script creates an local index by scanning the blockchain. This takes a *long* time, usually about 5 hours.  <br />
Subsequent runs will run much faster by looking at the differences.

### File Details
*config.env* - Environment config such as blockchain provider, smart contract address, index file and output file <br />
[DEFAULT] <br />
HttpProvider = https://core.bloxberg.org <br />
ContractAddress = 0x549A6E06BB2084100148D50F51CF77a3436C3Ae7 <br />
IndexFile = data.json <br />
CSVFile = nodes.csv <br />

*data.json* - Data dictionary with request ids and data processing request containing block number <br />

*nodes.csv* - Output of the script with the details of the nodes interacting with the smart contract <br />

*nodes.csv column details* <br />
[Column 01] = id <br />
[Column 02] = Wallet address <br />
[Column 03] = CPU Number of Cores <br />
[Column 04] = RAM <br />
[Column 05] = Storage <br />
[Column 06] = Bandwith <br />
[Column 07] = Max Duration of a running task <br />
[Column 08] = Status of a task <br />
[Column 09] = Cost for running a task <br />
[Column 10] = Created on: unix timestamp <br />
[Column 11] = Last updated on: unix timestamp <br />
