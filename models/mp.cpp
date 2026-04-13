#include <iostream>
#include <chrono>
#include <vector>
#include <algorithm>
#include <fstream>
#include <unordered_map>
#include <unordered_set>
#include <cmath> 
#include <iomanip>
#include <numeric>
#include <climits>

constexpr int MAX_USER_INST = 10001;
constexpr int MAX_N = 100000;
constexpr int MAX_M = 30;
constexpr int MAX_C = 2147483647;

struct Message {
    int msgType;
    int usrInst;
    int exeTime;
    int deadLine;
};

void stable_sort_usrInst_preserve_order(std::vector<Message>& messages) {
    int n = messages.size();
    for (int i = 0; i < n-1; i++) {
        for (int j = 0; j < n-i-1; j++) {
            if (messages[j].usrInst > messages[j+1].usrInst) {
                // Swap messages[j] and messages[j+1]
                Message temp = messages[j];
                messages[j] = messages[j+1];
                messages[j+1] = temp;
            }
        }
    }
}

void stable_sort_msgType_preserve_order(std::vector<Message>& messages) {
    int n = messages.size();
    for (int i = 0; i < n-1; i++) {
        for (int j = 0; j < n-i-1; j++) {
            if (messages[j].msgType > messages[j+1].msgType) {
                // Swap messages[j] and messages[j+1]
                Message temp = messages[j];
                messages[j] = messages[j+1];
                messages[j+1] = temp;
            }
        }
    }
}

void stable_sort_usrInst_preserve_relative_order(std::vector<Message>& messages) {
    int n = messages.size();
    for (int i = 1; i < n; i++) {
        Message key = messages[i];
        int j = i - 1;
        // Change the '>' operator to '>='
        while (j >= 0 && messages[j].usrInst >= key.usrInst) {
            messages[j + 1] = messages[j];
            j = j - 1;
        }
        messages[j + 1] = key;
    }
}

void sortCoreMsgType(std::vector<Message>& messages){
    int n = messages.size();
    for (int i = 0; i < n; i++) {
        Message key = messages[i];

        int j = i - 1;
        while (j >= 0 && messages[j].msgType != key.msgType && messages[j].usrInst != key.usrInst) {
            messages[j + 1] = messages[j];
            j = j - 1;
        }
        messages[j + 1] = key;
    }
}


std::vector<std::vector<Message>> simpleAssignCore(const std::vector<Message> &messages, int numCores, int c) {
    std::vector<std::vector<Message>> coreAssignments(numCores);
    std::vector<int> totalExecutionTime(numCores, 0);

    std::vector<int> usrInstToCore;
    int maxUsrInst = 0;
    for (const Message &message : messages) {
        maxUsrInst = std::max(maxUsrInst, message.usrInst);
    }
    usrInstToCore.assign(maxUsrInst + 1, -1);

    // Reserve space for vectors
    for (auto &coreAssignment : coreAssignments) {
        coreAssignment.reserve(messages.size() / numCores);
    }

    for (const Message &message : messages) {
        int coreToAssign;
        if (usrInstToCore[message.usrInst] == -1) {
            int minTotalTime = INT_MAX;
            int minCore = 0;
            for (int core = 0; core < numCores; ++core) {
                if (totalExecutionTime[core] + message.exeTime <= message.deadLine 
                    && totalExecutionTime[core] + message.exeTime <= c 
                    && totalExecutionTime[core] + message.exeTime < minTotalTime) {
                    minTotalTime = totalExecutionTime[core] + message.exeTime;
                    minCore = core;
                }
            }
            coreToAssign = minCore;
            usrInstToCore[message.usrInst] = minCore;
        } else {
            coreToAssign = usrInstToCore[message.usrInst];
        }

        coreAssignments[coreToAssign].emplace_back(message);
        totalExecutionTime[coreToAssign] += message.exeTime;
    }

    return coreAssignments;
}




void improveAffinity(std::vector<std::vector<Message>> &coreAssignments, int n) {
    
    for (auto &core_msgs : coreAssignments) {
        /*
        std::cout << "Before sorting: ";
        for (auto &msg : core_msgs) {
            std::cout << msg.msgType << " " << msg.usrInst << " ";
        }
        */
        
        sortCoreMsgType(core_msgs);
        
        /*
        std::cout << std::endl << "After sorting: ";
        for (auto &msg : core_msgs) {            
            std::cout << msg.msgType << " " << msg.usrInst << " ";
        }
        std::cout << std::endl;
        */
        
    }

}

double totalscore = 0;
double calculateScore(const std::vector<std::vector<Message>> &coreAssignments, int n);
void processMessages(int n, int m, int c, std::vector<Message> &messages) {
    std::vector<Message> original_messages = messages;
    /*
    for (const auto &msg : messages) {
        std::cout << msg.msgType << " " << msg.usrInst << " ";
    }
    std::cout << std::endl;
    */

    std::stable_sort(messages.begin(), messages.end(), [](const Message &a, const Message &b) {
        return a.usrInst < b.usrInst;
    });
    std::stable_sort(messages.begin(), messages.end(), [](const Message &a, const Message &b) {
        return a.deadLine < b.deadLine;
    });
    
    /*
    for (const auto &msg : messages) {
        std::cout << msg.msgType << " " << msg.usrInst << " ";
    }
    std::cout << std::endl;
    */

    std::vector<std::vector<Message>> coreAssignments;
    coreAssignments = simpleAssignCore(messages, m, c);

    improveAffinity(coreAssignments, n);
    improveAffinity(coreAssignments, n);
    

    //printf("Output:\n");
    /*
    for (const auto &core_msgs :coreAssignments) {
        std::cout << core_msgs.size() << " ";
        for (const auto &msg : core_msgs) {
            std::cout << msg.msgType << " " << msg.usrInst << " ";
        }
        std::cout << std::endl;
    }
    */

    printf("Result:\n");
    calculateScore(coreAssignments, n);
}

/*
int main() {
    int n, m, c;
    std::cin >> n >> m >> c;

    // Check constraints for n, m, c
    if (n < 1 || n > 100000) {
        std::cerr << "Invalid value for N. It should be in the range [1, 100000].\n";
        return 1;
    }
    if (m < 1 || m > 30) {
        std::cerr << "Invalid value for M. It should be in the range [1, 30].\n";
        return 1;
    }
    if (c < 1 || c > 2147483647) {
        std::cerr << "Invalid value for C. It should be in the range [1, 2147483647].\n";
        return 1;
    }

    std::vector<Message> messages(n);
    for (int i = 0; i < n; ++i) {
        std::cin >> messages[i].msgType >> messages[i].usrInst >> messages[i].exeTime >> messages[i].deadLine;

        // Check constraints for MsgType, UsrInst, ExeTime, and DeadLine
        if (messages[i].msgType < 1 || messages[i].msgType > 200) {
            std::cerr << "Invalid MsgType at line " << (i+1) << ". It should be in the range [1, 200].\n";
            return 1;
        }
        if (messages[i].usrInst < 1 || messages[i].usrInst > 10000) {
            std::cerr << "Invalid UsrInst at line " << (i+1) << ". It should be in the range [1, 10000].\n";
            return 1;
        }
        if (messages[i].exeTime < 1 || messages[i].exeTime > 2000) {
            std::cerr << "Invalid ExeTime at line " << (i+1) << ". It should be in the range [1, 2000].\n";
            return 1;
        }
        if (messages[i].deadLine < 1 || messages[i].deadLine > 1000000000) {
            std::cerr << "Invalid DeadLine at line " << (i+1) << ". It should be in the range [1, 10^9].\n";
            return 1;
        }
    }

    processMessages(n, m, c, messages);

    return 0;
}
*/

bool read_input_and_check_constraints(std::ifstream &file, int &n, int &m, int &c, std::vector<Message> &messages);
int main() {
    std::cout << "\nTest Case 01" << std::endl;
    int n, m, c;
    std::vector<Message> messages;
    std::ifstream file01("testcase01.txt");
    if (!read_input_and_check_constraints(file01, n, m, c, messages)) {
        return 1; 
    }

    auto start01 = std::chrono::high_resolution_clock::now(); 
    processMessages(n, m, c, messages);
    auto stop01 = std::chrono::high_resolution_clock::now();
    auto duration_m01 = std::chrono::duration_cast<std::chrono::microseconds>(stop01 - start01);
    std::cout << "Time: " << duration_m01.count() << " microseconds\n";

    //return 0;
    
    std::cout << "\ntestcase02" << std::endl;
    std::ifstream file02("testcase02.txt");
    if (!read_input_and_check_constraints(file02, n, m, c, messages)) {
        return 1; 
    }

    auto start02 = std::chrono::high_resolution_clock::now(); 
    processMessages(n, m, c, messages);
    auto stop02 = std::chrono::high_resolution_clock::now();
    auto duration_m02 = std::chrono::duration_cast<std::chrono::microseconds>(stop02 - start02);
    std::cout << "Time: " << duration_m02.count() << " microseconds\n";

    std::cout << "\ntestcase03" << std::endl;
    std::ifstream file03("testcase03.txt");
    if (!read_input_and_check_constraints(file03, n, m, c, messages)) {
        return 1; 
    }

    auto start03 = std::chrono::high_resolution_clock::now(); 
    processMessages(n, m, c, messages);
    auto stop03 = std::chrono::high_resolution_clock::now();
    auto duration_m03 = std::chrono::duration_cast<std::chrono::microseconds>(stop03 - start03);
    std::cout << "Time: " << duration_m03.count() << " microseconds\n";

    std::cout << "\ntestcase04" << std::endl;
    std::ifstream file04("testcase04.txt");
    if (!read_input_and_check_constraints(file04, n, m, c, messages)) {
        return 1; 
    }

   auto start04 = std::chrono::high_resolution_clock::now(); 
    processMessages(n, m, c, messages);
    auto stop04 = std::chrono::high_resolution_clock::now();
    auto duration_m04 = std::chrono::duration_cast<std::chrono::microseconds>(stop04 - start04);
    std::cout << "Time: " << duration_m04.count() << " microseconds\n";

    std::cout << "\ntestcase05" << std::endl;
    std::ifstream file05("testcase05.txt");
    if (!read_input_and_check_constraints(file05, n, m, c, messages)) {
        return 1; 
    }

   auto start05 = std::chrono::high_resolution_clock::now(); 
    processMessages(n, m, c, messages);
    auto stop05 = std::chrono::high_resolution_clock::now();
    auto duration_m05 = std::chrono::duration_cast<std::chrono::microseconds>(stop05 - start05);
    std::cout << "Time: " << duration_m05.count() << " microseconds\n";

    std::cout << "\ntestcase06" << std::endl;
    std::ifstream file06("testcase06.txt");
    if (!read_input_and_check_constraints(file06, n, m, c, messages)) {
        return 1; 
    }

    auto start06 = std::chrono::high_resolution_clock::now(); 
    processMessages(n, m, c, messages);
    auto stop06 = std::chrono::high_resolution_clock::now();
    auto duration_m06 = std::chrono::duration_cast<std::chrono::microseconds>(stop06 - start06);
    std::cout << "Time: " << duration_m06.count() << " microseconds\n";

    printf("\nTotal Score: %lf\n", floor(totalscore));
    int totaltime = duration_m01.count()+duration_m02.count()+duration_m03.count()+duration_m04.count()+duration_m05.count()+duration_m06.count();
    std::cout << "Total Time: " << totaltime << " microseconds\n";

      
    return 0;
}



double calculateScore(const std::vector<std::vector<Message>> &coreAssignments, int n) {
    int affinityScore = 0;
    int capabilityScore = 0;
    
    for (const auto &core_msgs : coreAssignments) {
        int previousMsgType = -1;
        int totalTimeForCore = 0;
        
        for (const auto &msg : core_msgs) {
            if (msg.msgType == previousMsgType) {
                affinityScore++;
            }
            totalTimeForCore += msg.exeTime;
            if (totalTimeForCore <= msg.deadLine) {
                capabilityScore++;
            }
            previousMsgType = msg.msgType;
        }
    }

    double score = ((affinityScore + capabilityScore) / (2.0 * n)) * 1e7;    
    totalscore += score;

    std::cout << std::fixed; // Use fixed-point notation
    std::cout << "capabilityScore: " << std::setprecision(2) << capabilityScore << std::endl;
    std::cout << "affinityScore: " << std::setprecision(2) << affinityScore << std::endl;
    std::cout << "Score: " << std::setprecision(2) << score << std::endl;     

    return score;
}

bool read_input_and_check_constraints(std::ifstream &file, int &n, int &m, int &c, std::vector<Message> &messages) {
    if (!file) {
        std::cerr << "Unable to open file.\n";
        return false;
    }

    file >> n >> m >> c;

    // Check constraints for n, m, c
    if (n < 1 || n > 100000) {
        std::cerr << "Invalid value for N. It should be in the range [1, 100000].\n";
        return false;
    }
    if (m < 1 || m > 30) {
        std::cerr << "Invalid value for M. It should be in the range [1, 30].\n";
        return false;
    }
    if (c < 1 || c > 2147483647) {
        std::cerr << "Invalid value for C. It should be in the range [1, 2147483647].\n";
        return false;
    }

    messages.resize(n);
    for (int i = 0; i < n; ++i) {
        file >> messages[i].msgType >> messages[i].usrInst >> messages[i].exeTime >> messages[i].deadLine;

        // Check constraints for MsgType, UsrInst, ExeTime, and DeadLine
        if (messages[i].msgType < 1 || messages[i].msgType > 200) {
            std::cerr << "Invalid MsgType at line " << (i+1) << ". It should be in the range [1, 200].\n";
            return false;
        }
        if (messages[i].usrInst < 1 || messages[i].usrInst > 10000) {
            std::cerr << "Invalid UsrInst at line " << (i+1) << ". It should be in the range [1, 10000].\n";
            return false;
        }
        if (messages[i].exeTime < 1 || messages[i].exeTime > 2000) {
            std::cerr << "Invalid ExeTime at line " << (i+1) << ". It should be in the range [1, 2000].\n";
            return false;
        }
        if (messages[i].deadLine < 1 || messages[i].deadLine > 1000000000) {
            std::cerr << "Invalid DeadLine at line " << (i+1) << ". It should be in the range [1, 10^9].\n";
            return false;
        }
    }

    return true;
}
