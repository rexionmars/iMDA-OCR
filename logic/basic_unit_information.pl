% Definição dos fatos dinâmicos para armazenar as informações
:- dynamic info/5.

% Regras para ordenar e montar a estrutura de informação
montar_unidade_info(Nome, Valor, Max, Min) :-
    findall(Info, info(Nome, _, Info, _, _), Infos),
    montar_lista_infos(Infos, Valor, Max, Min, Unidade),
    format('{~w: [~w]}', [Nome, Unidade]).

montar_lista_infos([], _, _, _, []).
montar_lista_infos([Info|Resto], Valor, Max, Min, [Unidade|OutrasUnidades]) :-
    montar_info(Info, Valor, Max, Min, Unidade),
    montar_lista_infos(Resto, Valor, Max, Min, OutrasUnidades).

montar_info([Label, Valor, Max, Min], Valor, Max, Min, Unidade) :-
    Unidade = '{"~w": {"currentValue": ~w, "maxValue": ~w, "minValue": ~w}}'-[Label, Valor, Max, Min].

% Exemplo de uso:
% Adicionar informações
adicionar_info(pulse, 'currentValue', 80).
adicionar_info(pulse, 'maxValue', 130).
adicionar_info(pulse, 'minValue', 50).

% Montar a unidade de informação
montar_unidade_info(pulse, Valor, Max, Min).
