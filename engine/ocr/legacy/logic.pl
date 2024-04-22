:- dynamic roi/5. % roi(ID, ROI_container, Label_region, Principal_value_region, Max_value_region, Min_value_region)

% Início do Programa
start_program :- 
    writeln('Selecione a região de interesse.'),
    % Lógica para exibir o texto acompanhando o mouse
    % Lógica para permitir a seleção do ROI_container

% Seleção do ROI Principal
select_roi_container(ROI_container) :-
    % Lógica para permitir a seleção do ROI_container
    assertz(roi(0, ROI_container, _, _, _, _)).

% Seleção do Label
select_label_region(Label_region) :-
    % Lógica para permitir a seleção da Label_region
    retract(roi(0, ROI_container, _, _, _, _)),
    assertz(roi(0, ROI_container, Label_region, _, _, _)).

% Seleção do Valor Principal
select_principal_value_region(Principal_value_region) :-
    % Lógica para permitir a seleção da Principal_value_region
    retract(roi(0, ROI_container, Label_region, _, _, _)),
    assertz(roi(0, ROI_container, Label_region, Principal_value_region, _, _)).

% Seleção do Valor Máximo
select_max_value_region(Max_value_region) :-
    % Lógica para permitir a seleção da Max_value_region
    retract(roi(0, ROI_container, Label_region, Principal_value_region, _, _)),
    assertz(roi(0, ROI_container, Label_region, Principal_value_region, Max_value_region, _)).

% Seleção do Valor Mínimo
select_min_value_region(Min_value_region) :-
    % Lógica para permitir a seleção da Min_value_region
    retract(roi(0, ROI_container, Label_region, Principal_value_region, Max_value_region, _)),
    assertz(roi(0, ROI_container, Label_region, Principal_value_region, Max_value_region, Min_value_region)).

