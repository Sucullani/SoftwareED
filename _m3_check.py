import ast
import education.mod03_constitutive as m
src = open('education/mod03_constitutive.py', encoding='utf-8').read()
ast.parse(src)
s = object.__new__(m.ConstitutiveModule)
txt = s._sandbox_text()
print('IMPORT OK')
print('sandbox len:', len(txt))
print('mentions D-de-tu:', 'D de tu' in txt)
print('diamond legend:', 'â—†' in txt)
print('contract color:', hasattr(m, '_CONTRACT_COLOR'))
print('probe caption removed:', 'respuesta a tracci' not in src)
print('isotropo note:', 'isótropo' in src)
print('no entry leftovers:', ('_var_nu' not in src) and ('_entry_nu' not in src))
