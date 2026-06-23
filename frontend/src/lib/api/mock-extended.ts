/**
 * Mock data for RAG teacher, skill-test, and study-plan APIs.
 *
 * Activated when VITE_API_MOCK=true.
 * Live mode will be fully wired in T22.
 */

import type {
  RagAnswerOut,
  RagSourceOut,
  SkillModuleOut,
  StudyPlanOut,
  PlanDay,
} from "@/types";

// ─── RAG Mock ──────────────────────────────────────────────────────────────

const mockRagSources: RagSourceOut[] = [
  {
    source_url: "https://rulesoftheroad.jp/s-curve.html",
    title: "S-Curve Maneuver Guide — Rules of the Road Japan",
    snippet:
      "The S-curve evaluates your ability to navigate two consecutive opposite-direction curves within a narrow corridor. Inner-wheel difference (nairinsa) is the primary hazard — rear wheels follow a tighter arc than front wheels.",
  },
  {
    source_url: "https://www.jaf.or.jp/en/driving/skill-test",
    title: "Practical Driving Test Overview — JAF",
    snippet:
      "The practical exam includes S-curve, crank, hill start, parallel parking, and other maneuvers. Maximum three corrections per obstacle. Touching boundary lines deducts five points; mounting the curb is instant failure.",
  },
];

const mockRagAnswer: RagAnswerOut = {
  answer:
    "The S-curve maneuver tests your ability to navigate two consecutive opposite-direction curves in a narrow corridor. The key challenge is inner-wheel difference (nairinsa) — your rear wheels follow a tighter arc than the front wheels. To succeed: (1) Enter the first curve from the outer edge of the lane, (2) Steer smoothly and gradually, (3) Monitor rear wheel clearance through side mirrors, (4) Straighten the wheel at the transition point, (5) Exit the second curve centered. You are allowed a maximum of three corrections. Touching the curb deducts five points; mounting it is instant failure.",
  sources: mockRagSources,
};

const mockRagRefusal: RagAnswerOut = {
  answer:
    "I can only answer questions related to the Japanese driver's license test — including traffic rules, road signs, driving maneuvers, and exam procedures. Your question appears to be outside this scope. Please try asking about a specific driving rule, skill test maneuver, or exam requirement.",
  sources: [],
};

// ─── Skill Module Mock ─────────────────────────────────────────────────────

const mockSkillModules: SkillModuleOut[] = [
  {
    id: 1,
    slug: "s-curve",
    name_en: "S-Curve",
    name_pt: "Curva em S",
    sort_order: 1,
    overview_en:
      "The S-curve maneuver evaluates your ability to navigate two consecutive opposite-direction curves within a narrow corridor. The core challenge is managing inner-wheel difference (nairinsa).",
    overview_pt:
      "A manobra de curva em S avalia sua capacidade de navegar duas curvas consecutivas em direções opostas dentro de um corredor estreito. O desafio principal é gerenciar a diferença de trajetória das rodas traseiras (nairinsa).",
    svg_path: "assets/skill/s-curve-diagram.svg",
    correct_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 450 }, { x: 50, y: 380 }, { x: 60, y: 340 },
        { x: 90, y: 300 }, { x: 130, y: 265 }, { x: 170, y: 245 },
        { x: 210, y: 235 }, { x: 250, y: 230 }, { x: 290, y: 235 },
        { x: 330, y: 250 }, { x: 370, y: 275 }, { x: 400, y: 310 },
        { x: 425, y: 350 }, { x: 440, y: 390 }, { x: 450, y: 430 },
        { x: 450, y: 450 },
      ],
    }),
    wrong_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 450 }, { x: 65, y: 400 }, { x: 90, y: 350 },
        { x: 110, y: 310 }, { x: 125, y: 280 }, { x: 140, y: 260 },
        { x: 170, y: 245 }, { x: 210, y: 230 }, { x: 260, y: 240 },
        { x: 310, y: 260 }, { x: 350, y: 290 }, { x: 380, y: 330 },
        { x: 410, y: 380 }, { x: 430, y: 420 }, { x: 450, y: 450 },
      ],
      failure_reason_en:
        "Steering into the first curve too early causes the rear wheels to cut inside and mount the curb. The driver then over-corrects, losing position for the second curve.",
      failure_reason_pt:
        "Esterçar para a primeira curva muito cedo faz as rodas traseiras cortarem por dentro e subirem no meio-fio. O motorista então corrige demais, perdendo o posicionamento para a segunda curva.",
    }),
    common_mistakes_json: JSON.stringify({
      en: [
        "Entering the first curve from the center of the lane instead of the outer edge",
        "Turning the steering wheel too sharply at the apex",
        "Using all three allowed corrections before finishing",
        "Accelerating through the curves instead of maintaining a steady crawl",
        "Failing to check side mirrors to monitor rear wheel position",
      ],
      pt: [
        "Entrar na primeira curva pelo centro da faixa em vez da borda externa",
        "Girar o volante muito bruscamente no ápice",
        "Usar todas as três correções permitidas antes de terminar",
        "Acelerar durante as curvas em vez de manter velocidade constante",
        "Não verificar os retrovisores laterais para monitorar as rodas traseiras",
      ],
    }),
    checklist_json: JSON.stringify([
      { step: 1, text: { en: "Approach the S-curve at a slow, steady speed in first or second gear", pt: "Aproxime-se da curva em S com velocidade lenta e constante em primeira ou segunda marcha" }, pass_criteria: { en: "Vehicle speed is walking pace or slower, engine RPM stable", pt: "Velocidade do veículo igual ou menor que passo de caminhada, RPM do motor estável" } },
      { step: 2, text: { en: "Position the vehicle toward the outer edge of the lane before the first curve", pt: "Posicione o veículo em direção à borda externa da faixa antes da primeira curva" }, pass_criteria: { en: "Vehicle is within 30cm of the outer lane edge, centered laterally", pt: "Veículo está a até 30cm da borda externa da faixa, centralizado lateralmente" } },
      { step: 3, text: { en: "Begin steering smoothly as the front bumper reaches the curve entrance, not before", pt: "Comece a esterçar suavemente quando o para-choque dianteiro atingir a entrada da curva, não antes" }, pass_criteria: { en: "Steering input is gradual, no sudden wheel movements", pt: "Esterçamento é gradual, sem movimentos bruscos no volante" } },
      { step: 4, text: { en: "Monitor rear wheel clearance through side mirrors during both curves", pt: "Monitore a folga das rodas traseiras pelos retrovisores laterais durante ambas as curvas" }, pass_criteria: { en: "Rear wheels maintain at least 10cm clearance from the curb throughout", pt: "Rodas traseiras mantêm pelo menos 10cm de folga do meio-fio durante todo o percurso" } },
      { step: 5, text: { en: "Straighten the wheel at the transition point between the two curves", pt: "Endireite o volante no ponto de transição entre as duas curvas" }, pass_criteria: { en: "Vehicle is centered in the lane at the midpoint, wheels straight", pt: "Veículo está centralizado na faixa no ponto médio, rodas retas" } },
      { step: 6, text: { en: "Exit the second curve smoothly and accelerate only after clearing the course", pt: "Saia da segunda curva suavemente e acelere apenas após liberar o percurso" }, pass_criteria: { en: "Vehicle exits centered, no curb contact, within correction limit", pt: "Veículo sai centralizado, sem contato com meio-fio, dentro do limite de correções" } },
    ]),
    pro_tip_en:
      "Think of the rear wheels as the ones that matter, not the front, since they are what will hit the curb first.",
    pro_tip_pt:
      "Pense nas rodas traseiras como as que importam, não nas dianteiras, pois são elas que vão atingir o meio-fio primeiro.",
  },
  {
    id: 2,
    slug: "crank",
    name_en: "Crank",
    name_pt: "Curva de 90 Graus",
    sort_order: 2,
    overview_en:
      "The crank maneuver tests your ability to execute sharp 90-degree turns in an extremely confined space. The lane width is barely wider than the vehicle itself.",
    overview_pt:
      "A manobra de curva de 90 graus testa sua capacidade de executar curvas fechadas em um espaço extremamente confinado. A largura da faixa é pouco maior que o próprio veículo.",
    svg_path: "assets/skill/crank-diagram.svg",
    correct_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 450 }, { x: 50, y: 300 }, { x: 50, y: 250 },
        { x: 100, y: 200 }, { x: 200, y: 150 }, { x: 300, y: 150 },
        { x: 450, y: 150 },
      ],
    }),
    wrong_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 450 }, { x: 50, y: 320 }, { x: 80, y: 260 },
        { x: 120, y: 220 }, { x: 180, y: 180 }, { x: 300, y: 160 },
        { x: 450, y: 150 },
      ],
      failure_reason_en:
        "Not using the full width of the lane before starting the turn causes the rear wheels to strike the inner corner of the crank.",
      failure_reason_pt:
        "Não usar toda a largura da faixa antes de iniciar a curva faz as rodas traseiras atingirem o canto interno da curva de 90.",
    }),
    common_mistakes_json: JSON.stringify({
      en: [
        "Not performing a visual check behind the vehicle before beginning the turn",
        "Starting the turn too early without using the full lane width",
        "Focusing only on the front of the car and forgetting the rear end swings wide",
        "Exceeding three corrections during the maneuver",
      ],
      pt: [
        "Não fazer verificação visual atrás do veículo antes de iniciar a curva",
        "Iniciar a curva muito cedo sem usar toda a largura da faixa",
        "Focar apenas na frente do carro e esquecer que a traseira balança para fora",
        "Exceder três correções durante a manobra",
      ],
    }),
    checklist_json: JSON.stringify([
      { step: 1, text: { en: "Approach the crank at walking speed", pt: "Aproxime-se da curva de 90 em velocidade de caminhada" }, pass_criteria: { en: "Speed is slow and controlled", pt: "Velocidade é lenta e controlada" } },
      { step: 2, text: { en: "Stop and check behind the vehicle before starting the turn", pt: "Pare e verifique atrás do veículo antes de iniciar a curva" }, pass_criteria: { en: "Full visual check of rear and sides completed", pt: "Verificação visual completa de trás e laterais concluída" } },
      { step: 3, text: { en: "Position the vehicle at the outer edge of the lane", pt: "Posicione o veículo na borda externa da faixa" }, pass_criteria: { en: "Vehicle uses full lane width for maximum turning radius", pt: "Veículo usa toda a largura da faixa para máximo raio de curva" } },
      { step: 4, text: { en: "Execute the 90-degree turn smoothly", pt: "Execute a curva de 90 graus suavemente" }, pass_criteria: { en: "No boundary contact, rear wheels clear the inner corner", pt: "Sem contato com limites, rodas traseiras liberam o canto interno" } },
    ]),
    pro_tip_en:
      "Always check behind you before starting the turn — examiners specifically watch for this.",
    pro_tip_pt:
      "Sempre verifique atrás antes de iniciar a curva — os examinadores observam isso especificamente.",
  },
  {
    id: 3,
    slug: "hill-start",
    name_en: "Hill Start",
    name_pt: "Partida em Subida",
    sort_order: 3,
    overview_en:
      "The hill start tests your ability to move off from a stopped position on an incline without rolling backward. You must coordinate clutch, accelerator, and handbrake.",
    overview_pt:
      "A partida em subida testa sua capacidade de sair de uma posição parada em uma inclinação sem rolar para trás. Você deve coordenar embreagem, acelerador e freio de mão.",
    svg_path: "assets/skill/hill-start-diagram.svg",
    correct_trajectory_json: JSON.stringify({
      path: [
        { x: 100, y: 400 }, { x: 100, y: 380 }, { x: 110, y: 350 },
        { x: 130, y: 300 }, { x: 160, y: 250 }, { x: 200, y: 200 },
        { x: 250, y: 150 },
      ],
    }),
    wrong_trajectory_json: JSON.stringify({
      path: [
        { x: 100, y: 400 }, { x: 100, y: 420 }, { x: 100, y: 410 },
        { x: 110, y: 380 }, { x: 140, y: 320 }, { x: 180, y: 250 },
        { x: 250, y: 150 },
      ],
      failure_reason_en:
        "Releasing the handbrake before finding the bite point causes the vehicle to roll backward before forward motion begins.",
      failure_reason_pt:
        "Soltar o freio de mão antes de encontrar o ponto de fricção faz o veículo rolar para trás antes de iniciar o movimento para frente.",
    }),
    common_mistakes_json: JSON.stringify({
      en: [
        "Releasing the handbrake too early before the clutch bites",
        "Rolling backward more than a few centimeters",
        "Stalling the engine by releasing the clutch too quickly",
        "Revving the engine excessively before finding the bite point",
      ],
      pt: [
        "Soltar o freio de mão muito cedo antes da embreagem pegar",
        "Rolar para trás mais de alguns centímetros",
        "Enguiar o motor soltando a embreagem muito rápido",
        "Acelerar excessivamente antes de encontrar o ponto de fricção",
      ],
    }),
    checklist_json: JSON.stringify([
      { step: 1, text: { en: "Stop on the incline and apply the handbrake firmly", pt: "Pare na subida e aplique o freio de mão firmemente" }, pass_criteria: { en: "Vehicle is stationary, handbrake fully engaged", pt: "Veículo está parado, freio de mão totalmente acionado" } },
      { step: 2, text: { en: "Find the clutch bite point while applying gentle throttle", pt: "Encontre o ponto de fricção da embreagem aplicando acelerador suave" }, pass_criteria: { en: "Engine note changes, slight vibration felt", pt: "Som do motor muda, leve vibração sentida" } },
      { step: 3, text: { en: "Release the handbrake smoothly while holding the bite point", pt: "Solte o freio de mão suavemente mantendo o ponto de fricção" }, pass_criteria: { en: "No backward movement, vehicle begins to move forward", pt: "Sem movimento para trás, veículo começa a mover para frente" } },
      { step: 4, text: { en: "Accelerate smoothly and fully release the clutch", pt: "Acelere suavemente e solte completamente a embreagem" }, pass_criteria: { en: "Smooth acceleration, no stall, no rollback", pt: "Aceleração suave, sem enguiar, sem rolar para trás" } },
    ]),
    pro_tip_en:
      "Practice finding the bite point on flat ground first — muscle memory is everything on a hill.",
    pro_tip_pt:
      "Pratique encontrar o ponto de fricção em terreno plano primeiro — a memória muscular é tudo em uma subida.",
  },
  {
    id: 4,
    slug: "parallel-parking",
    name_en: "Parallel Parking",
    name_pt: "Estacionamento Paralelo",
    sort_order: 4,
    overview_en:
      "Parallel parking tests your ability to reverse into a parking space between two vehicles. The space is approximately 1.5 times the length of your vehicle.",
    overview_pt:
      "O estacionamento paralelo testa sua capacidade de dar ré em uma vaga entre dois veículos. O espaço é aproximadamente 1,5 vezes o comprimento do seu veículo.",
    svg_path: "assets/skill/parallel-parking-diagram.svg",
    correct_trajectory_json: JSON.stringify({
      path: [
        { x: 400, y: 350 }, { x: 350, y: 340 }, { x: 300, y: 320 },
        { x: 250, y: 280 }, { x: 200, y: 250 }, { x: 150, y: 250 },
        { x: 100, y: 250 },
      ],
    }),
    wrong_trajectory_json: JSON.stringify({
      path: [
        { x: 400, y: 350 }, { x: 320, y: 330 }, { x: 260, y: 290 },
        { x: 200, y: 240 }, { x: 150, y: 230 }, { x: 100, y: 230 },
      ],
      failure_reason_en:
        "Turning the wheel too early causes the vehicle to enter the space at too sharp an angle, hitting the front car's rear bumper.",
      failure_reason_pt:
        "Virar o volante muito cedo faz o veículo entrar na vaga em um ângulo muito fechado, batendo no para-choque traseiro do carro da frente.",
    }),
    common_mistakes_json: JSON.stringify({
      en: [
        "Starting the reverse turn too early before aligning with the front car",
        "Not checking behind before reversing",
        "Turning the steering wheel too sharply",
        "Finishing at an angle rather than parallel to the curb",
      ],
      pt: [
        "Iniciar a curva de ré muito cedo antes de alinhar com o carro da frente",
        "Não verificar atrás antes de dar ré",
        "Virar o volante muito bruscamente",
        "Terminar em ângulo em vez de paralelo ao meio-fio",
      ],
    }),
    checklist_json: JSON.stringify([
      { step: 1, text: { en: "Pull alongside the front car, leaving about 50cm gap", pt: "Encoste ao lado do carro da frente, deixando cerca de 50cm de espaço" }, pass_criteria: { en: "Vehicle is parallel to front car, safe gap maintained", pt: "Veículo está paralelo ao carro da frente, espaço seguro mantido" } },
      { step: 2, text: { en: "Check all mirrors and behind before reversing", pt: "Verifique todos os retrovisores e atrás antes de dar ré" }, pass_criteria: { en: "Full 360-degree visual check completed", pt: "Verificação visual completa de 360 graus concluída" } },
      { step: 3, text: { en: "Reverse slowly, turning the wheel when rear aligns with front car's bumper", pt: "Dê ré lentamente, virando o volante quando a traseira alinhar com o para-choque do carro da frente" }, pass_criteria: { en: "Smooth arc, no contact with either car", pt: "Arco suave, sem contato com nenhum carro" } },
      { step: 4, text: { en: "Straighten the wheel and center the vehicle in the space", pt: "Endireite o volante e centralize o veículo no espaço" }, pass_criteria: { en: "Vehicle is parallel to curb, centered between cars", pt: "Veículo está paralelo ao meio-fio, centralizado entre os carros" } },
    ]),
    pro_tip_en:
      "Use your reference points — when the rear of your car aligns with the front car's bumper, that's your signal to turn.",
    pro_tip_pt:
      "Use seus pontos de referência — quando a traseira do seu carro alinha com o para-choque do carro da frente, é o sinal para virar.",
  },
  {
    id: 5,
    slug: "sudden-stop",
    name_en: "Sudden Stop",
    name_pt: "Parada Brusca",
    sort_order: 5,
    overview_en:
      "The sudden stop maneuver tests your ability to bring the vehicle to a complete, controlled stop within a short distance without locking the wheels or losing directional control.",
    overview_pt:
      "A manobra de parada brusca testa sua capacidade de parar o veículo completamente e de forma controlada em uma curta distância sem travar as rodas ou perder o controle direcional.",
    svg_path: "assets/skill/sudden-stop-diagram.svg",
    correct_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 250 }, { x: 150, y: 250 }, { x: 250, y: 250 },
        { x: 300, y: 250 }, { x: 310, y: 250 },
      ],
    }),
    wrong_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 250 }, { x: 150, y: 250 }, { x: 250, y: 250 },
        { x: 300, y: 240 }, { x: 310, y: 230 },
      ],
      failure_reason_en:
        "Braking too hard locks the wheels, causing the vehicle to skid and lose directional control.",
      failure_reason_pt:
        "Frear muito forte trava as rodas, fazendo o veículo derrapar e perder o controle direcional.",
    }),
    common_mistakes_json: JSON.stringify({
      en: [
        "Slamming the brakes causing wheel lock and skid",
        "Not checking mirrors before braking",
        "Failing to depress the clutch before the brake, causing engine stall",
        "Stopping past the designated stop line",
      ],
      pt: [
        "Pisar forte no freio causando travamento das rodas e derrapagem",
        "Não verificar os retrovisores antes de frear",
        "Não pisar na embreagem antes do freio, causando enguiar do motor",
        "Parar além da linha de parada designada",
      ],
    }),
    checklist_json: JSON.stringify([
      { step: 1, text: { en: "Check mirrors before braking", pt: "Verifique os retrovisores antes de frear" }, pass_criteria: { en: "Mirror check completed before brake application", pt: "Verificação dos retrovisores concluída antes de aplicar o freio" } },
      { step: 2, text: { en: "Depress the clutch, then apply firm progressive braking", pt: "Pise na embreagem, depois aplique frenagem firme e progressiva" }, pass_criteria: { en: "No wheel lock, no skid, smooth deceleration", pt: "Sem travamento de rodas, sem derrapagem, desaceleração suave" } },
      { step: 3, text: { en: "Bring the vehicle to a complete stop at the designated line", pt: "Pare o veículo completamente na linha designada" }, pass_criteria: { en: "Vehicle stops at or before the stop line, no overshoot", pt: "Veículo para na ou antes da linha de parada, sem ultrapassar" } },
    ]),
    pro_tip_en:
      "Depress the clutch a fraction before the brake — this prevents engine stall and gives you smoother control.",
    pro_tip_pt:
      "Pise na embreagem uma fração antes do freio — isso evita enguiar o motor e dá controle mais suave.",
  },
  {
    id: 6,
    slug: "pedestrian-crossing",
    name_en: "Pedestrian Crossing",
    name_pt: "Faixa de Pedestres",
    sort_order: 6,
    overview_en:
      "The pedestrian crossing maneuver tests your ability to safely approach, stop, and proceed through a crosswalk while yielding to pedestrians.",
    overview_pt:
      "A manobra de faixa de pedestres testa sua capacidade de se aproximar, parar e prosseguir por uma faixa de pedestres com segurança, cedendo passagem aos pedestres.",
    svg_path: "assets/skill/pedestrian-crossing-diagram.svg",
    correct_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 250 }, { x: 150, y: 250 }, { x: 200, y: 250 },
        { x: 200, y: 250 }, { x: 250, y: 250 }, { x: 350, y: 250 },
      ],
    }),
    wrong_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 250 }, { x: 150, y: 250 }, { x: 200, y: 250 },
        { x: 220, y: 250 }, { x: 350, y: 250 },
      ],
      failure_reason_en:
        "Failing to come to a complete stop before the crosswalk when a pedestrian is present, or proceeding before the pedestrian has fully cleared the crossing.",
      failure_reason_pt:
        "Não parar completamente antes da faixa de pedestres quando um pedestre está presente, ou prosseguir antes de o pedestre cruzar completamente.",
    }),
    common_mistakes_json: JSON.stringify({
      en: [
        "Not coming to a complete stop before the crosswalk",
        "Proceeding before the pedestrian has fully cleared the crossing",
        "Not checking both sides for approaching pedestrians",
        "Stopping on or past the crosswalk stop line",
      ],
      pt: [
        "Não parar completamente antes da faixa de pedestres",
        "Prosseguir antes de o pedestre cruzar completamente",
        "Não verificar ambos os lados para pedestres se aproximando",
        "Parar sobre ou além da linha de parada da faixa",
      ],
    }),
    checklist_json: JSON.stringify([
      { step: 1, text: { en: "Approach the crosswalk at reduced speed", pt: "Aproxime-se da faixa de pedestres em velocidade reduzida" }, pass_criteria: { en: "Speed is reduced well before the crossing", pt: "Velocidade é reduzida bem antes da faixa" } },
      { step: 2, text: { en: "Check both sides for pedestrians", pt: "Verifique ambos os lados para pedestres" }, pass_criteria: { en: "Full visual check of both approaches", pt: "Verificação visual completa de ambas as aproximações" } },
      { step: 3, text: { en: "Stop completely before the stop line if pedestrians are present", pt: "Pare completamente antes da linha de parada se houver pedestres" }, pass_criteria: { en: "Full stop, vehicle behind the stop line", pt: "Parada completa, veículo atrás da linha de parada" } },
      { step: 4, text: { en: "Proceed only after all pedestrians have cleared the crossing", pt: "Prossiga apenas após todos os pedestres cruzarem completamente" }, pass_criteria: { en: "No pedestrians in or approaching the crossing", pt: "Sem pedestres na ou se aproximando da faixa" } },
    ]),
    pro_tip_en:
      "Even if no pedestrians are visible, slow down — examiners want to see caution, not just compliance.",
    pro_tip_pt:
      "Mesmo se não houver pedestres visíveis, reduza a velocidade — os examinadores querem ver cautela, não apenas conformidade.",
  },
  {
    id: 7,
    slug: "railroad-crossing",
    name_en: "Railroad Crossing",
    name_pt: "Passagem de Nível",
    sort_order: 7,
    overview_en:
      "The railroad crossing maneuver tests your ability to safely approach, stop, look, and proceed through a railroad crossing.",
    overview_pt:
      "A manobra de passagem de nível testa sua capacidade de se aproximar, parar, olhar e prosseguir por uma passagem de nível com segurança.",
    svg_path: "assets/skill/railroad-crossing-diagram.svg",
    correct_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 250 }, { x: 150, y: 250 }, { x: 200, y: 250 },
        { x: 200, y: 250 }, { x: 250, y: 250 }, { x: 350, y: 250 },
      ],
    }),
    wrong_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 250 }, { x: 200, y: 250 }, { x: 250, y: 250 },
        { x: 350, y: 250 },
      ],
      failure_reason_en:
        "Failing to come to a complete stop and look both ways before proceeding through the crossing.",
      failure_reason_pt:
        "Não parar completamente e olhar ambos os lados antes de prosseguir pela passagem.",
    }),
    common_mistakes_json: JSON.stringify({
      en: [
        "Not coming to a complete stop before the crossing",
        "Not looking both ways before proceeding",
        "Entering the crossing when there is not enough space on the other side",
        "Stopping on the tracks",
      ],
      pt: [
        "Não parar completamente antes da passagem",
        "Não olhar ambos os lados antes de prosseguir",
        "Entrar na passagem quando não há espaço suficiente do outro lado",
        "Parar sobre os trilhos",
      ],
    }),
    checklist_json: JSON.stringify([
      { step: 1, text: { en: "Approach the crossing at reduced speed", pt: "Aproxime-se da passagem em velocidade reduzida" }, pass_criteria: { en: "Speed is reduced, vehicle is under control", pt: "Velocidade é reduzida, veículo está sob controle" } },
      { step: 2, text: { en: "Stop completely before the crossing and look both ways", pt: "Pare completamente antes da passagem e olhe ambos os lados" }, pass_criteria: { en: "Full stop, visual check of both directions", pt: "Parada completa, verificação visual de ambas as direções" } },
      { step: 3, text: { en: "Confirm there is enough space beyond the crossing before proceeding", pt: "Confirme que há espaço suficiente além da passagem antes de prosseguir" }, pass_criteria: { en: "Clear space confirmed on the far side", pt: "Espaço livre confirmado do outro lado" } },
      { step: 4, text: { en: "Proceed smoothly and clear the crossing without stopping on tracks", pt: "Prossiga suavemente e libere a passagem sem parar sobre os trilhos" }, pass_criteria: { en: "Vehicle clears the crossing without stopping", pt: "Veículo libera a passagem sem parar" } },
    ]),
    pro_tip_en:
      "Always stop and look — even if the barrier is up and no train is visible. Examiners check for this habit.",
    pro_tip_pt:
      "Sempre pare e olhe — mesmo se a barreira estiver aberta e não houver trem visível. Os examinadores verificam esse hábito.",
  },
  {
    id: 8,
    slug: "general-driving",
    name_en: "General Driving",
    name_pt: "Direção Geral",
    sort_order: 8,
    overview_en:
      "General driving evaluates your overall vehicle control, lane discipline, speed management, and situational awareness throughout the test course.",
    overview_pt:
      "A direção geral avalia seu controle geral do veículo, disciplina de faixa, gerenciamento de velocidade e consciência situacional ao longo do percurso de teste.",
    svg_path: "assets/skill/general-driving-diagram.svg",
    correct_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 400 }, { x: 150, y: 380 }, { x: 250, y: 350 },
        { x: 350, y: 300 }, { x: 400, y: 200 }, { x: 450, y: 100 },
      ],
    }),
    wrong_trajectory_json: JSON.stringify({
      path: [
        { x: 50, y: 400 }, { x: 160, y: 370 }, { x: 270, y: 340 },
        { x: 360, y: 290 }, { x: 410, y: 190 }, { x: 450, y: 100 },
      ],
      failure_reason_en:
        "Inconsistent speed and wandering within the lane without smooth corrections throughout the course.",
      failure_reason_pt:
        "Velocidade inconsistente e vagar dentro da faixa sem correções suaves ao longo do percurso.",
    }),
    common_mistakes_json: JSON.stringify({
      en: [
        "Inconsistent speed throughout the course",
        "Wandering within the lane instead of maintaining a steady position",
        "Not checking mirrors regularly",
        "Jerky steering inputs instead of smooth corrections",
      ],
      pt: [
        "Velocidade inconsistente ao longo do percurso",
        "Vagar dentro da faixa em vez de manter posição estável",
        "Não verificar os retrovisores regularmente",
        "Esterçamento brusco em vez de correções suaves",
      ],
    }),
    checklist_json: JSON.stringify([
      { step: 1, text: { en: "Maintain a steady, appropriate speed throughout the course", pt: "Mantenha velocidade estável e apropriada ao longo do percurso" }, pass_criteria: { en: "Speed is consistent and within limits", pt: "Velocidade é consistente e dentro dos limites" } },
      { step: 2, text: { en: "Keep the vehicle centered in the lane at all times", pt: "Mantenha o veículo centralizado na faixa em todos os momentos" }, pass_criteria: { en: "No wandering, smooth position corrections", pt: "Sem vagar, correções de posição suaves" } },
      { step: 3, text: { en: "Check mirrors every 5-8 seconds", pt: "Verifique os retrovisores a cada 5-8 segundos" }, pass_criteria: { en: "Regular mirror checks observed", pt: "Verificações regulares de retrovisores observadas" } },
      { step: 4, text: { en: "Use smooth, deliberate steering inputs", pt: "Use esterçamento suave e deliberado" }, pass_criteria: { en: "No jerky movements, all inputs are smooth", pt: "Sem movimentos bruscos, todas as entradas são suaves" } },
    ]),
    pro_tip_en:
      "Drive as if you're carrying a full cup of coffee — smoothness is the name of the game.",
    pro_tip_pt:
      "Dirija como se estivesse carregando uma xícara de café cheia — suavidade é o nome do jogo.",
  },
];

// ─── Study Plan Mock ───────────────────────────────────────────────────────

function generateMockStudyPlan(days: number): StudyPlanOut {
  const planDays: PlanDay[] = [];
  const today = new Date();

  const themeDistribution: number[][] = [
    [1, 2], [3, 4], [1, 5], [2, 6], [3, 7], [4, 8], [1, 2, 3],
    [5, 6], [7, 8], [1, 4], [2, 5], [3, 6], [7, 1], [8, 2],
  ];

  const focusNotesEn = [
    "Focus on S-curve and crank — the two most common fail points",
    "Hill start and parallel parking — practice clutch control",
    "Review traffic signs and right-of-way rules",
    "Crank and sudden stop — precision braking practice",
    "Pedestrian crossing and railroad — safety procedures",
    "General driving — smoothness and mirror checks",
    "S-curve and parallel parking — combine maneuver practice",
    "Hill start and general driving — speed management",
    "Railroad crossing and pedestrian — situational awareness",
    "Traffic signs and crank — visual recognition under pressure",
    "Right-of-way and parallel parking — judgment practice",
    "S-curve and hill start — combine two hardest maneuvers",
    "General driving and pedestrian — full course simulation",
    "All maneuvers — final review day",
  ];

  const focusNotesPt = [
    "Foque na curva em S e curva de 90 — os dois pontos mais comuns de reprovação",
    "Partida em subida e estacionamento paralelo — pratique controle de embreagem",
    "Revise placas de trânsito e regras de preferência",
    "Curva de 90 e parada brusca — prática de frenagem precisa",
    "Faixa de pedestres e passagem de nível — procedimentos de segurança",
    "Direção geral — suavidade e verificações de retrovisor",
    "Curva em S e estacionamento paralelo — combine prática de manobras",
    "Partida em subida e direção geral — gerenciamento de velocidade",
    "Passagem de nível e pedestres — consciência situacional",
    "Placas de trânsito e curva de 90 — reconhecimento visual sob pressão",
    "Preferência e estacionamento paralelo — prática de julgamento",
    "Curva em S e partida em subida — combine as duas manobras mais difíceis",
    "Direção geral e pedestres — simulação de percurso completo",
    "Todas as manobras — dia de revisão final",
  ];

  for (let i = 0; i < days; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    const themes = themeDistribution[i % themeDistribution.length];
    const noteIdx = i % focusNotesEn.length;
    planDays.push({
      date: date.toISOString().split("T")[0],
      theme_ids: themes,
      question_count: 15 + (i % 10),
      focus_note_en: focusNotesEn[noteIdx],
      focus_note_pt: focusNotesPt[noteIdx],
    });
  }

  return {
    id: Date.now(),
    created_at: today.toISOString(),
    source: "default-beginner",
    days: planDays,
  };
}

const mockStudyPlanHistory: StudyPlanOut[] = [
  generateMockStudyPlan(7),
  generateMockStudyPlan(5),
];

// ─── Exported mock data ────────────────────────────────────────────────────

export {
  mockRagAnswer,
  mockRagRefusal,
  mockRagSources,
  mockSkillModules,
  generateMockStudyPlan,
  mockStudyPlanHistory,
};