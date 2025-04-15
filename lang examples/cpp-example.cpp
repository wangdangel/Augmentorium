#include <iostream>
#include <vector>
#include <algorithm>

#include <boost/algorithm/string.hpp>
#include <nlohmann/json.hpp>
#include <fmt/format.h>

using json = nlohmann::json;

class DataProcessor {
private:
    std::vector<std::string> data;

public:
    DataProcessor(const std::vector<std::string>& input_data) : data(input_data) {}

    void process() {
        // Convert to lowercase using Boost
        for (auto& item : data) {
            boost::algorithm::to_lower(item);
        }
        
        // Sort the data
        std::sort(data.begin(), data.end());
        
        // Output formatted data
        for (const auto& item : data) {
            std::cout << fmt::format("Processed item: {}", item) << std::endl;
        }
    }
};

int main() {
    std::vector<std::string> input = {"Apple", "Banana", "Cherry"};
    DataProcessor processor(input);
    processor.process();
    return 0;
}