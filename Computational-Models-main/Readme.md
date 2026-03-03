This project contains libraries that we have implemented in Python for working with computation models: finite automatons (including automatons with null transitions), regular expressions, context-free grammars, and automatons with a stack. Specifically, we have implemented the main algorithms in each one of the representation models. The project also includes Jupyter Notebooks for checking the algorithms and practicing some exercises. 

We describe below each one of the files of the project in detail: 

- **AFND.py**: It contains a class with the main attributes and operations for Non-Deterministic Finite Automatons (NDFA).
- **TransitionFunction.py**: The class with the operations and methods for transitions in NDFA is included in this file. 
- **AFND\_nullable.py**: This file includes a class with the operations for NDFAs with null transitions. Such a class extends the one corresponding to NDFAs. 
- **AFD\_to\_reg.py**: It includes the required operations for converting a Finite Deterministic Automaton (DFA) to a regular expression. 
- **reg\_to\_postfix**: In this file, auxiliary methods employed to convert a DFA to a regular expression can be found. 
- **reg\_to\_AFND.py**: This file contains all necessary methods to obtain an NDFA with null transitions from a regular expression. 
- **automaton\_linear\_grammar.py**: In this file, we include all essential operations to obtain a linear grammar (by the left or by the right) from an NDFA and vice-versa. 
- **production\_rule.py**: The class that contains the main attributes and methods for production rules in context-free grammars is allocated in this file. 
- **grammar.py**: This file includes a class with the attributes and algorithms for working with context-free grammars. 
- **Transition\_Stack.py**: This file contains the class with the attributes and methods of the transitions of automatons with a stack. 
- **automatonStack.py**: The class with the attributes and methods for automatons with a stack can be found in this file.
- **AutomatonStack\_ICGrammar.py**: The required methods for obtaining an automaton with a stack from a context-free grammar and vice-versa are included in this file. 
- **Utils.py**: The auxiliary functions for implementing the aforementioned libraries can be found in this file. 
- **tests.py**: This file is used to test the methods implemented in the Python libraries. 
- **Automaton\_Regular\_expression.ipynb**: This file corresponds to a Jupyter Notebook for practicing with NDFAs (including NDFAs with null transitions), DFAs, regular expressions, and linear by the left and right grammars. 
- **Operations\_automatons.ipynb**: This Jupyter Notebook allows us to test the main operations with regular languages (languages accepted by a DFA). 
- **Grammar.ipynb**: It shows how to check the main operations with context-free grammars. 
- **Automaton_Stack.ipynb**: This file is associated with the Jupyter Notebook that illustrates how to use the main methods with automatons with a stack. 
- **Operations\_CF\_languages.ipynb**: It contains the Jupyter Notebook that lets us practice with context-free languages (languages accepted by a context-free grammar or, equivalently, by an automaton with a stack). 
- **\*.txt files**: These files contain the examples employed for illustrating the algorithms in the Jupyter Notebooks. 