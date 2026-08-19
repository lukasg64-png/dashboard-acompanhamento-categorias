const path = require('path');
const fs = require('fs');
const { fetchTableData } = require(path.join(__dirname, '..', '..', 'projeto-base-qlik', 'src', 'qlik'));

process.env.QLIK_URL = 'https://sense.farmaciassaojoao.com.br';
process.env.QLIK_USERNAME = 'lucas.alves6';
process.env.QLIK_PASSWORD = 'Eloise2025*';
process.env.QLIK_APP_ID = '671fa4f4-eb7d-418f-b4c9-936e87d8011d';

async function main() {
  console.log('Iniciando extração da tabela ZKJqXsu do Qlik Sense...');
  const outputPath = path.join(__dirname, '..', 'data', 'qlik_agosto_extracted.jsonl');
  
  try {
    const rowCount = await fetchTableData({
      qlikAppId: '671fa4f4-eb7d-418f-b4c9-936e87d8011d',
      qlikObjectId: 'ZKJqXsu',
      writeToFilePath: outputPath,
      limitRows: 50 // Testar primeiras 50 linhas
    });
    
    console.log(`Sucesso! ${rowCount} linhas gravadas em ${outputPath}`);
    
    const lines = fs.readFileSync(outputPath, 'utf8').trim().split('\n');
    console.log('Exemplo de linha extraída:');
    console.log(JSON.stringify(JSON.parse(lines[0]), null, 2));
  } catch (err) {
    console.error('Erro na extração:', err.message);
  }
}

main();
