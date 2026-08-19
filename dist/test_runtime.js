
const fs = require('fs');
const s0 = fs.readFileSync('c:/Users/lucas.alves6/OneDrive - Farmácias São João/Documentos/ANTIGRAVITI/dashboard-acompanhamento-categorias/dist/test_script_0.js', 'utf8');
const s1 = fs.readFileSync('c:/Users/lucas.alves6/OneDrive - Farmácias São João/Documentos/ANTIGRAVITI/dashboard-acompanhamento-categorias/dist/test_script_1.js', 'utf8');

// Mock DOM elements
global.document = {
  addEventListener: () => {},
  getElementById: (id) => ({
    addEventListener: () => {},
    querySelectorAll: () => [],
    classList: { add: () => {}, remove: () => {}, toggle: () => {} },
    style: {},
    innerHTML: '',
    textContent: '',
    value: 'ALL'
  }),
  querySelectorAll: () => []
};
global.window = { print: () => {} };

try {
  eval(s0);
  console.log('Script 0 executed without error!');
  eval(s1);
  console.log('Script 1 executed without error!');
} catch (e) {
  console.error('RUNTIME ERROR:', e);
}
