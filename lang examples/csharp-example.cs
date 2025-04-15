using System;
using System.Collections.Generic;
using System.Linq;

// Import necessary namespaces
using System; // Provides fundamental classes and base types
using System.Collections.Generic; // Provides generic collection classes
using System.Linq; // Provides LINQ (Language Integrated Query) capabilities

// Define the main namespace for the application
namespace SimpleCSharpApp
{
    // Define the main class for the program
    class Program
    {
        // The main entry point of the application
        static void Main(string[] args)
        {
            // Call the GreetUser function
            GreetUser("Alice");

            // Create a list of numbers
            List<int> numbers = new List<int> { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };

            // Use LINQ to get even numbers
            List<int> evenNumbers = GetEvenNumbers(numbers);

            // Display the even numbers
            Console.WriteLine("\nEven numbers in the list:");
            foreach (int num in evenNumbers)
            {
                Console.Write(num + " "); // Output: 2 4 6 8 10
            }
            Console.WriteLine(); // Add a newline for better formatting

            // Keep the console window open until a key is pressed (optional)
            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }

        /// <summary>
        /// Greets the user by name.
        /// </summary>
        /// <param name="name">The name of the user to greet.</param>
        static void GreetUser(string name)
        {
            // Print a greeting message to the console
            Console.WriteLine($"Hello, {name}! Welcome to the simple C# app.");
        }

        /// <summary>
        /// Filters a list of integers to return only the even numbers.
        /// </summary>
        /// <param name="inputList">The list of integers to filter.</param>
        /// <returns>A new list containing only the even numbers from the input list.</returns>
        static List<int> GetEvenNumbers(List<int> inputList)
        {
            // Use LINQ's Where extension method to filter for even numbers
            // n => n % 2 == 0 is a lambda expression that checks if a number is even
            List<int> evenList = inputList.Where(n => n % 2 == 0).ToList();

            // Return the filtered list
            return evenList;
        }
    }
}
