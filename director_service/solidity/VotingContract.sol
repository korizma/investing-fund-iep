// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

contract VotingContract 
{
    address[] private voters;
    uint voted_yes;
    uint voted_no;
    constructor(address[] memory _voters) 
    {
        voters = _voters;
        voted_yes = 0;
        voted_no = 0;
    }

    function decisionFinalized() public view returns (int) 
    {
        if (voted_yes > voters.length /2)
            return 1;
        
        if (voted_no > voters.length /2)
            return -1;

        return 0;
    }

    function vote(bool approve) public  
    {
        require(decisionFinalized() == 0, "Voting ended.");

        uint i;
        bool exists = false;
        for (i = 0; i < voters.length; i++) 
        {
            if (voters[i] == msg.sender)
            {
                exists = true;
                break;
            }
        }

        require(exists, "Invalid address.");

        delete voters[i];

        if (approve)
            voted_yes += 1;
        else
            voted_no += 1;
    }
}