### What is Node Explorer?
Ethernity Cloud node explorer is a script which provides an easy way to find all the nodes which interacted with Ethernity Cloud's smart contract. <br />
The explorer's purpose is to be integrated in various dashboards to get a visual representation about nodes activity. <br />

### Requirements
python >= 3.5 (Find out which version is installed by running "python3 -V") <br />
web3 module >=4.0 (Find out which is installed by running "pip show web3") <br />

### Ubuntu Instructions
Below commands are installing the prerequsites and clone the repository
|Bash Instructions| 
| -------------|
|**sudo** apt install python3 pip -y|
|pip install web3|
|git clone https://github.com/ethernity-cloud/etny-node-explorer|

### Running
Launch the script with "**python3 nodes_reader.py**".  <br />
The script works by scanning the blockchain for nodes which interacts with the smart contract and saves the output to a CSV file. <br />
When ran for the first time the script creates an local index by scanning the blockchain. This takes a *long* time, usually about 5 hours.  <br />
Subsequent runs will run much faster by looking at the differences.

### File Details
*config.env* - Environment config such as blockchain provider, smart contract address, index file and output file <br />
| config.env| 
| ------------- |
|[DEFAULT]|
|HttpProvider = https://core.bloxberg.org|
|ContractAddress = *0x549A6E06BB2084100148D50F51CF77a3436C3Ae7*|
|IndexFile = data.json|
|CSVFile = nodes.csv|

*data.json* - Data dictionary with request ids and data processing request containing block number <br />

*nodes.csv* - Output of the script with the details of the nodes interacting with the smart contract <br />

*nodes.csv column details* <br />

| Column 01  | Column 02 | Column 03 | Column 04 | Column 05 | Column 06 | Column 07 | Column 08 | Column 09 | Column 10 |Column   11|
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
|id|wallet address|CPU*|RAM|Storage|Bandwith   |Task*|Status*|Cost*|Created*|Last updated*|


_*CPU_ = CPU Number of Cores <br />
_*Task_ = Max Duration of a running task <br />
_*Status_ = Status of a task <br />
_*Cost_ = Cost for running a task <br />
_*Created_ = Created on: unix timestamp <br />
_*Last updated_ = Last updated on: unix timestamp <br />
