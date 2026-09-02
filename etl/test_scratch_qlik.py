import json

with open('data/setembro/curva_diaria.json', 'r', encoding='utf-8') as f:
    curva = json.load(f)

print("Dia | Dia Semana | Peso Ponderado | % do Dia | % Acumulado | Meta Acumulada R$")
print("-" * 80)
for c in curva:
    print("{:>3} | {:<10} | {:>14.4f} | {:>7.3f}% | {:>10.3f}% | R$ {:>14,.2f}".format(
        c['dia'], c['dia_semana'], c['peso'], c['pct_dia']*100, c['pct_acum']*100, c['meta_acum']
    ))
