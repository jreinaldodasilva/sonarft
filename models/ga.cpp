#include <iostream>
#include <chrono>
#include <vector>
#include <algorithm>
#include <fstream>
#include <unordered_map>
#include <unordered_set>
#include <cmath> 
#include <queue> // Include for priority_queue
#include <iomanip>
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

struct Chromosome {
    std::vector<int> core_to_user;
    double affinityScore;
    double capabilityScore;
    double score;
    std::vector<std::vector<Message>> coreAssignments;  
};

std::vector<Chromosome> initializePopulation(int populationSize, int m, int MAX_USER_INST) {
    std::vector<Chromosome> population;
    population.reserve(populationSize);
    for (int i = 0; i < populationSize; ++i) {
        Chromosome chromosome;
        chromosome.core_to_user.resize(MAX_USER_INST, -1);
        chromosome.affinityScore = 0.0;
        chromosome.capabilityScore = 0.0;
        chromosome.score = 0.0;
        population.emplace_back(chromosome);
    }
    return population;
}

double totalscore = 0;

Chromosome& tournamentSelection(std::vector<Chromosome> &population, int tournamentSize) {
    std::vector<Chromosome*> tournament(tournamentSize);
    for(int i = 0; i < tournamentSize; ++i) {
        int index = rand() % population.size();
        tournament[i] = &population[index];
    }
    return **std::max_element(tournament.begin(), tournament.end(), [](const Chromosome* a, const Chromosome* b) {
        return a->score < b->score;
    });
}

Chromosome rouletteWheelSelection(std::vector<Chromosome> &population) {
    double totalFitness = 0.0;
    for (const auto &chromosome : population) {
        totalFitness += chromosome.score;
    }
    double randomPoint = static_cast<double>(rand()) / RAND_MAX * totalFitness;
    double accumulated = 0.0;
    for (const auto &chromosome : population) {
        accumulated += chromosome.score;
        if (accumulated >= randomPoint) {
            return chromosome;
        }
    }
    return population.back();
}

#include <random>

std::mt19937 gen(std::random_device{}());

Chromosome crossover(const Chromosome &parent1, const Chromosome &parent2, int MAX_USER_INST, int m) {
    Chromosome child;
    child.core_to_user.resize(MAX_USER_INST, -1);

    std::uniform_int_distribution<> dis(0, 1);
    for (int i = 0; i < MAX_USER_INST; ++i) {
        child.core_to_user[i] = (dis(gen) == 0) ? parent1.core_to_user[i] : parent2.core_to_user[i];
    }

    return child;
}

void mutate(Chromosome &child, int m, int MAX_USER_INST) {
    std::uniform_real_distribution<> dis(0, 1);
    std::uniform_int_distribution<> disInt(0, m-1);
    for (int i = 0; i < MAX_USER_INST; ++i) {
        if (dis(gen) < 0.6) {  // 15% mutation rate
            child.core_to_user[i] = disInt(gen);  // Assign a random core
        }
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

std::vector<std::vector<Message>> assignCore(const std::vector<Message> &messages, int numCores, int c) {
    std::vector<std::vector<Message>> coreAssignments(numCores);
    std::vector<int> totalExecutionTime(numCores, 0);

    int maxUsrInst = 0;
    for (const Message &message : messages) {
        maxUsrInst = std::max(maxUsrInst, message.usrInst);
    }
    std::vector<int> usrInstToCore(maxUsrInst + 1, -1);

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

double calculateScore(Chromosome &chromosome, const std::vector<std::vector<Message>> &coreAssignments, int n) {
    int affinityScore = 0;
    int capabilityScore = 0;
    
    for (const auto &core_msgs : coreAssignments) {
        int previousMsgType = -1;
        int totalTimeForCore = 0;
        
        for (const auto &msg : core_msgs) {
            if (msg.msgType == previousMsgType) {
                chromosome.affinityScore++;
            }
            totalTimeForCore += msg.exeTime;
            if (totalTimeForCore <= msg.deadLine) {
                chromosome.capabilityScore++;
            }
            previousMsgType = msg.msgType;
        }
    }
    
    double score = ((chromosome.affinityScore + chromosome.capabilityScore) / (2.0 * n)) * 1e7;
    chromosome.score = score;
    return score;
}

Chromosome geneticAlgorithm(int n, int m, int c, std::vector<Message> &messages) {
    std::vector<Message> sortedMessages = messages; // Make a copy
    std::sort(messages.begin(), messages.end(), [](const Message &a, const Message &b) {
        return a.usrInst < b.usrInst;
    });
    
    int generations = 6; //m;
    int populationSize = 6;
    int tournamentSize = 600; 

    std::vector<Chromosome> population = initializePopulation(populationSize, m, MAX_USER_INST);
    std::stable_sort(messages.begin(), messages.end(), [](const Message &a, const Message &b) {
        return a.usrInst < b.usrInst;
    });
    std::stable_sort(messages.begin(), messages.end(), [](const Message &a, const Message &b) {
        return a.deadLine < b.deadLine;
    });
    for (auto &chromosome : population) {
        chromosome.coreAssignments = assignCore(sortedMessages, m, c);
        improveAffinity(chromosome.coreAssignments, n);

        calculateScore(chromosome, chromosome.coreAssignments, n);
    }
    std::sort(population.begin(), population.end(), [](const Chromosome &a, const Chromosome &b) {
        return a.score > b.score;
    });  
    
    Chromosome bestEver = population[0];

    for (int generation = 0; generation < generations; ++generation) {
        
        if(population[0].score > bestEver.score) {
            bestEver = population[0];
        }

        std::vector<Chromosome> newPopulation;
        while (newPopulation.size() < populationSize) {  
            
            Chromosome& parent1 = tournamentSelection(population, tournamentSize); 
            Chromosome& parent2 = tournamentSelection(population, tournamentSize);
            
            Chromosome child = crossover(parent1, parent2, MAX_USER_INST, m);
            
            mutate(child, m, MAX_USER_INST);
            
            newPopulation.push_back(child);
        }

        for (auto &chromosome : population) {
            chromosome.coreAssignments = assignCore(sortedMessages, m, c);
            improveAffinity(chromosome.coreAssignments, n);

            calculateScore(chromosome, chromosome.coreAssignments, n);
        }
        
        std::sort(newPopulation.begin(), newPopulation.end(), [](const Chromosome &a, const Chromosome &b) {
            return a.score > b.score;
        });

        population = std::move(newPopulation);
        
    }
    
    return bestEver;
}

void displayResultsAndMetrics(const Chromosome &chromosome);
/*
int main() {
    srand(time(0));
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

    Chromosome gaSolution = geneticAlgorithm(n, m, c, messages);
    displayResultsAndMetrics(gaSolution);

    return 0;
}
*/


void displayResultsAndMetrics(const Chromosome &chromosome) {
    // Output the results
    /*
    for (const auto &core_msgs : chromosome.coreAssignments) {
        std::cout << core_msgs.size() << " ";
        for (const auto &msg : core_msgs) {
            std::cout << msg.msgType << " " << msg.usrInst << " ";
        }
        std::cout << std::endl;
    }
    */

    
    double affinityScore = chromosome.affinityScore;
    double capabilityScore = chromosome.capabilityScore;
    double score = chromosome.score;
    totalscore += score;

    std::cout << std::fixed; // Use fixed-point notation
    std::cout << "capabilityScore: " << std::setprecision(2) << capabilityScore << std::endl;
    std::cout << "affinityScore: " << std::setprecision(2) << affinityScore << std::endl;
    std::cout << "Score: " << std::setprecision(2) << score << std::endl;    
    

}

bool read_input_and_check_constraints(std::ifstream &file, int &n, int &m, int &c, std::vector<Message> &messages);
int main() {
    srand(time(NULL));
    std::cout << "\ntestcase01" << std::endl;
    int n, m, c;
    std::vector<Message> messages;
    std::ifstream file01("testcase01.txt");
    if (!read_input_and_check_constraints(file01, n, m, c, messages)) {
        return 1; 
    }
    auto start01 = std::chrono::high_resolution_clock::now(); 

    Chromosome gaSolution = geneticAlgorithm(n, m, c, messages);
    displayResultsAndMetrics(gaSolution);

    auto stop01 = std::chrono::high_resolution_clock::now();
    auto duration_m01 = std::chrono::duration_cast<std::chrono::microseconds>(stop01 - start01);
    std::cout << "Time: " << duration_m01.count() << " microseconds\n";

    std::cout << "\ntestcase02" << std::endl;
    std::ifstream file02("testcase02.txt");
    if (!read_input_and_check_constraints(file02, n, m, c, messages)) {
        return 1; 
    }
    auto start02 = std::chrono::high_resolution_clock::now(); 
    Chromosome gaSolution2 = geneticAlgorithm(n, m, c, messages);
    displayResultsAndMetrics(gaSolution2);
    auto stop02 = std::chrono::high_resolution_clock::now();
    auto duration_m02 = std::chrono::duration_cast<std::chrono::microseconds>(stop02 - start02);
    std::cout << "Time: " << duration_m02.count() << " microseconds\n";


    std::cout << "\ntestcase03" << std::endl;
    std::ifstream file03("testcase03.txt");
    if (!read_input_and_check_constraints(file03, n, m, c, messages)) {
        return 1; 
    }
    auto start03 = std::chrono::high_resolution_clock::now(); 
    Chromosome gaSolution3 = geneticAlgorithm(n, m, c, messages);
    displayResultsAndMetrics(gaSolution3);
    auto stop03 = std::chrono::high_resolution_clock::now();
    auto duration_m03 = std::chrono::duration_cast<std::chrono::microseconds>(stop03 - start03);
    std::cout << "Time: " << duration_m03.count() << " microseconds\n";


    std::cout << "\ntestcase04" << std::endl;
    std::ifstream file04("testcase04.txt");
    if (!read_input_and_check_constraints(file04, n, m, c, messages)) {
        return 1; 
    }
    auto start04 = std::chrono::high_resolution_clock::now(); 
    Chromosome gaSolution4 = geneticAlgorithm(n, m, c, messages);
    displayResultsAndMetrics(gaSolution4);
    auto stop04 = std::chrono::high_resolution_clock::now();
    auto duration_m04 = std::chrono::duration_cast<std::chrono::microseconds>(stop04 - start04);
    std::cout << "Time: " << duration_m04.count() << " microseconds\n";


    std::cout << "\ntestcase05" << std::endl;
    std::ifstream file05("testcase05.txt");
    if (!read_input_and_check_constraints(file05, n, m, c, messages)) {
        return 1; 
    }
    auto start05 = std::chrono::high_resolution_clock::now(); 
    Chromosome gaSolution5 = geneticAlgorithm(n, m, c, messages);
    displayResultsAndMetrics(gaSolution5);
    auto stop05 = std::chrono::high_resolution_clock::now();
    auto duration_m05 = std::chrono::duration_cast<std::chrono::microseconds>(stop05 - start05);
    std::cout << "Time: " << duration_m05.count() << " microseconds\n";


    std::cout << "\ntestcase06" << std::endl;
    std::ifstream file06("testcase06.txt");
    if (!read_input_and_check_constraints(file06, n, m, c, messages)) {
        return 1; 
    }
    auto start06 = std::chrono::high_resolution_clock::now(); 
    Chromosome gaSolution6 = geneticAlgorithm(n, m, c, messages);
    displayResultsAndMetrics(gaSolution6);
    auto stop06 = std::chrono::high_resolution_clock::now();
    auto duration_m06 = std::chrono::duration_cast<std::chrono::microseconds>(stop06 - start06);
    std::cout << "Time: " << duration_m06.count() << " microseconds\n";

    printf("\nTotal Score: %lf\n", floor(totalscore));
    int totaltime = duration_m01.count()+duration_m02.count()+duration_m03.count()+duration_m04.count()+duration_m05.count()+duration_m06.count();
    std::cout << "Total Time: " << totaltime << " microseconds\n";

    return 0;
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
