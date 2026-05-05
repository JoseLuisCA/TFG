import sys
from pathlib import Path
# Ensure the library folder is on sys.path so AFND can import TransitionFunction
sys.path.insert(0, str(Path(__file__).resolve().parent / 'library'))
from AFND import FiniteAutomaton

fa = FiniteAutomaton.readAutomaton('automatons/automaton3.txt')
print('Before:')
for t in fa.getTransitionFunction():
    print(t.getInitialState(), repr(t.getInputSymbol()), t.getFinalStates())

# simulate that q3 is an error state (in automaton3 q0 already points to q3)
print('\nStates before clean:', fa.getStatesSet())
print('Calling deleteInaccessibleStates()...')
fa.deleteInaccessibleStates()
print('Returned from deleteInaccessibleStates()')
print('Calling deleteErrorStates()...')
fa.deleteErrorStates()
print('Returned from deleteErrorStates()')
print('\nAfter clean:')
for t in fa.getTransitionFunction():
    print(t.getInitialState(), repr(t.getInputSymbol()), t.getFinalStates())
print('States:', fa.getStatesSet())
print('Finals:', fa.getFinalStates())
