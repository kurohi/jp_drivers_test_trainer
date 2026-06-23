/**
 * Mock data provider for offline development.
 *
 * Returns 22 themes + realistic questions WITHOUT answers (QuestionListItem)
 * and WITH answers (QuestionDetail) for explanation reveal.
 *
 * Activated when VITE_API_MOCK=true.
 */

import type {
  ThemeOut,
  QuestionListItem,
  QuestionDetail,
  Difficulty,
} from "@/types";

// ─── 22 Official Japanese Driver's License Test Themes ───────────────────

export const mockThemes: ThemeOut[] = [
  { id: 1, slug: "traffic-signs", name_en: "Traffic Signs & Markings", name_pt: "Placas de Trânsito & Marcas", parent_id: null, sort_order: 1 },
  { id: 2, slug: "right-of-way", name_en: "Right of Way", name_pt: "Preferência", parent_id: null, sort_order: 2 },
  { id: 3, slug: "speed-regulations", name_en: "Speed Regulations", name_pt: "Regulamentação de Velocidade", parent_id: null, sort_order: 3 },
  { id: 4, slug: "overtaking-passing", name_en: "Overtaking & Passing", name_pt: "Ultrapassagem", parent_id: null, sort_order: 4 },
  { id: 5, slug: "railroad-crossings", name_en: "Railroad Crossings", name_pt: "Passagens de Nível", parent_id: null, sort_order: 5 },
  { id: 6, slug: "intersections", name_en: "Intersections", name_pt: "Interseções", parent_id: null, sort_order: 6 },
  { id: 7, slug: "pedestrians-bicycles", name_en: "Pedestrians & Bicycles", name_pt: "Pedestres & Bicicletas", parent_id: null, sort_order: 7 },
  { id: 8, slug: "parking-stopping", name_en: "Parking & Stopping", name_pt: "Estacionamento & Parada", parent_id: null, sort_order: 8 },
  { id: 9, slug: "emergency-vehicles", name_en: "Emergency Vehicles", name_pt: "Veículos de Emergência", parent_id: null, sort_order: 9 },
  { id: 10, slug: "vehicle-inspection", name_en: "Vehicle Inspection", name_pt: "Inspeção do Veículo", parent_id: null, sort_order: 10 },
  { id: 11, slug: "driver-obligations", name_en: "Driver Obligations", name_pt: "Obrigações do Motorista", parent_id: null, sort_order: 11 },
  { id: 12, slug: "license-regulations", name_en: "License Regulations", name_pt: "Regulamentação de Carteira", parent_id: null, sort_order: 12 },
  { id: 13, slug: "traffic-violations", name_en: "Traffic Violations", name_pt: "Infrações de Trânsito", parent_id: null, sort_order: 13 },
  { id: 14, slug: "expressway-driving", name_en: "Expressway Driving", name_pt: "Direção em Rodovia", parent_id: null, sort_order: 14 },
  { id: 15, slug: "night-driving", name_en: "Night Driving", name_pt: "Direção Noturna", parent_id: null, sort_order: 15 },
  { id: 16, slug: "adverse-weather", name_en: "Adverse Weather Driving", name_pt: "Direção em Clima Adverso", parent_id: null, sort_order: 16 },
  { id: 17, slug: "vehicle-loading", name_en: "Vehicle Dimensions & Loading", name_pt: "Dimensões & Carga do Veículo", parent_id: null, sort_order: 17 },
  { id: 18, slug: "towing", name_en: "Towing", name_pt: "Reboque", parent_id: null, sort_order: 18 },
  { id: 19, slug: "seat-belts-child-seats", name_en: "Seat Belts & Child Seats", name_pt: "Cintos & Cadeirinhas", parent_id: null, sort_order: 19 },
  { id: 20, slug: "mobile-phone-use", name_en: "Mobile Phone Use", name_pt: "Uso de Celular", parent_id: null, sort_order: 20 },
  { id: 21, slug: "drinking-driving", name_en: "Drinking & Driving", name_pt: "Álcool & Direção", parent_id: null, sort_order: 21 },
  { id: 22, slug: "first-aid-accidents", name_en: "First Aid & Accidents", name_pt: "Primeiros Socorros & Acidentes", parent_id: null, sort_order: 22 },
];

// ─── Question pool generator ───────────────────────────────────────────────
// Generates realistic questions per theme. List items have NO answer fields.
// Detail items add answer_en/answer_pt/explanation_en/explanation_pt.

const PROMPTS: Record<number, { en: string; pt: string; answer: "true" | "false"; exp_en: string; exp_pt: string; tricky?: boolean; pattern?: string; difficulty?: Difficulty }[]> = {
  1: [ // traffic-signs
    { en: "A flashing yellow traffic signal means you must come to a complete stop before proceeding.", pt: "Um sinal amarelo intermitente significa que você deve parar completamente antes de prosseguir.", answer: "false", exp_en: "A flashing yellow signal means slow down and proceed with caution, not a complete stop. A flashing red requires a full stop.", exp_pt: "Um sinal amarelo intermitente significa reduzir a velocidade e prosseguir com atenção, não parar completamente. O vermelho intermitente exige parada total." },
    { en: "A triangular warning sign with a red border indicates a hazard ahead.", pt: "Uma placa triangular de advertência com borda vermelha indica um perigo à frente.", answer: "true", exp_en: "Triangular signs with red borders are warning signs indicating hazards such as curves, intersections, or pedestrian crossings ahead.", exp_pt: "Placas triangulares com bordas vermelhas são placas de advertência indicando perigos como curvas, interseções ou passagens de pedestres à frente." },
    { en: "A blue circular sign is a regulatory sign that prohibits certain actions.", pt: "Uma placa circular azul é uma placa regulamentadora que proíbe certas ações.", answer: "false", exp_en: "Blue circular signs are mandatory instruction signs (e.g., 'go straight only'). Red circular signs with a slash are prohibitory.", exp_pt: "Placas circulares azuis são placas de instrução obrigatória (ex: 'siga em frente'). Placas circulares vermelhas com barra são proibitivas.", tricky: true, pattern: "color-confusion" },
    { en: "You may ignore a stop sign if there is no visible traffic in either direction.", pt: "Você pode ignorar uma placa de pare se não houver tráfego visível em nenhuma direção.", answer: "false", exp_en: "A stop sign requires a complete stop regardless of visible traffic. Failing to stop is a violation even with no other vehicles present.", exp_pt: "A placa de pare exige parada completa independentemente do tráfego visível. Não parar é uma infração mesmo sem outros veículos presentes." },
    { en: "A no-parking sign with an arrow pointing in both directions means no parking on both sides of the sign.", pt: "Uma placa de proibido estacionar com seta em ambas as direções significa proibido estacionar nos dois lados da placa.", answer: "true", exp_en: "Double arrows on a no-parking sign indicate the restriction applies to both directions from the sign's location.", exp_pt: "Setas duplas em uma placa de proibido estacionar indicam que a restrição se aplica a ambas as direções a partir da localização da placa." },
  ],
  2: [ // right-of-way
    { en: "At an uncontrolled intersection, the vehicle on the left has the right of way.", pt: "Em uma interseção sem sinalização, o veículo à esquerda tem preferência.", answer: "false", exp_en: "At an uncontrolled intersection of equal roads, the vehicle on the RIGHT has right of way in Japan (left-hand traffic rules apply differently).", exp_pt: "Em uma interseção sem sinalização de vias iguais, o veículo à DIREITA tem preferência no Japão (regras de tráfego mão esquerda se aplicam diferentemente).", tricky: true, pattern: "left-right-confusion" },
    { en: "Emergency vehicles with sirens always have absolute right of way, even when driving against traffic.", pt: "Veículos de emergência com sirenes sempre têm preferência absoluta, mesmo dirigindo contra o tráfego.", answer: "false", exp_en: "Emergency vehicles have priority but must still follow basic traffic safety. They cannot recklessly drive against traffic without caution.", exp_pt: "Veículos de emergência têm prioridade mas ainda devem seguir a segurança básica de trânsito. Não podem dirigir contra o tráfego sem cautela." },
    { en: "When a funeral procession is passing, you must yield even if you have a green light.", pt: "Quando um cortejo fúnebre está passando, você deve ceder passagem mesmo com sinal verde.", answer: "true", exp_en: "In Japan, funeral processions have customary right of way. Drivers are expected to stop and allow them to pass out of respect.", exp_pt: "No Japão, cortejos fúnebres têm preferência por costume. Espera-se que os motoristas parem e permitam sua passagem por respeito." },
    { en: "A vehicle already in a roundabout must yield to vehicles entering the roundabout.", pt: "Um veículo já em um rotatório deve ceder passagem aos veículos que entram.", answer: "false", exp_en: "Vehicles entering a roundabout must yield to vehicles already circulating within it. This is the fundamental roundabout rule.", exp_pt: "Veículos que entram em um rotatório devem ceder passagem aos veículos já circulando nele. Esta é a regra fundamental dos rotatórios." },
  ],
  3: [ // speed-regulations
    { en: "The maximum speed limit on ordinary roads in Japan is 60 km/h unless otherwise posted.", pt: "O limite máximo de velocidade em vias comuns no Japão é 60 km/h, salvo sinalização em contrário.", answer: "true", exp_en: "The statutory speed limit on ordinary (non-expressway) roads in Japan is 60 km/h. Lower limits are often posted in urban areas.", exp_pt: "O limite de velocidade estatutário em vias comuns (não rodovias) no Japão é 60 km/h. Limites menores são frequentemente sinalizados em áreas urbanas." },
    { en: "You may exceed the speed limit by up to 10 km/h when overtaking another vehicle.", pt: "Você pode exceder o limite de velocidade em até 10 km/h ao ultrapassar outro veículo.", answer: "false", exp_en: "The speed limit is absolute. You may not exceed it for any reason, including overtaking. You must complete the pass within the speed limit.", exp_pt: "O limite de velocidade é absoluto. Você não pode excedê-lo por nenhum motivo, incluindo ultrapassagem. Deve completar a manobra dentro do limite." },
    { en: "In residential areas with a 30 km/h zone sign, all roads within that zone have a 30 km/h limit.", pt: "Em áreas residenciais com placa de zona 30 km/h, todas as vias dentro da zona têm limite de 30 km/h.", answer: "true", exp_en: "A 30 km/h zone sign establishes a zone-wide speed limit. All roads within the designated area are subject to the 30 km/h limit.", exp_pt: "A placa de zona 30 km/h estabelece um limite de velocidade para toda a zona. Todas as vias dentro da área designada estão sujeitas ao limite de 30 km/h." },
    { en: "Speed limits on expressways are suggestions and can be safely exceeded in good weather.", pt: "Limites de velocidade em rodovias são sugestões e podem ser excedidos com segurança em bom clima.", answer: "false", exp_en: "Speed limits are legal maximums, not suggestions. Exceeding them is a traffic violation regardless of weather conditions.", exp_pt: "Limites de velocidade são máximos legais, não sugestões. Excedê-los é uma infração de trânsito independentemente das condições climáticas." },
  ],
  4: [ // overtaking-passing
    { en: "You may overtake another vehicle on a curve with a solid center line if visibility is clear.", pt: "Você pode ultrapassar outro veículo em uma curva com linha central contínua se a visibilidade estiver boa.", answer: "false", exp_en: "A solid center line prohibits overtaking regardless of visibility. Curves with solid lines are specifically marked because overtaking is dangerous there.", exp_pt: "Uma linha central contínua proíbe ultrapassagem independentemente da visibilidade. Curvas com linhas contínuas são assim marcadas porque ultrapassar é perigoso." },
    { en: "When being overtaken, you should reduce speed to help the other vehicle complete the pass safely.", pt: "Ao ser ultrapassado, você deve reduzir a velocidade para ajudar o outro veículo a completar a ultrapassagem com segurança.", answer: "true", exp_en: "When being overtaken, you must not accelerate. Reducing speed helps the passing vehicle complete the maneuver safely and is required by law.", exp_pt: "Ao ser ultrapassado, você não deve acelerar. Reduzir a velocidade ajuda o veículo que ultrapassa a completar a manobra com segurança e é exigido por lei." },
    { en: "Overtaking is permitted within 30 meters before a pedestrian crossing.", pt: "A ultrapassagem é permitida a até 30 metros antes de uma faixa de pedestres.", answer: "false", exp_en: "Overtaking is prohibited within 30 meters before a pedestrian crossing (crosswalk). This zone ensures pedestrian safety.", exp_pt: "A ultrapassagem é proibida a até 30 metros antes de uma faixa de pedestres. Esta zona garante a segurança dos pedestres." },
    { en: "You may overtake a streetcar on the right side only when there is sufficient space.", pt: "Você pode ultrapassar um bonde pelo lado direito apenas quando houver espaço suficiente.", answer: "true", exp_en: "Streetcars (trams) should normally be overtaken on the right. Sufficient space and clear visibility are required for safe passing.", exp_pt: "Bondes (vlt) normalmente devem ser ultrapassados pela direita. Espaço suficiente e visibilidade clara são necessários para ultrapassagem segura." },
  ],
  5: [ // railroad-crossings
    { en: "You must stop before a railroad crossing even if the barrier is open and no train is visible.", pt: "Você deve parar antes de uma passagem de nível mesmo se a barreira estiver aberta e não houver trem visível.", answer: "false", exp_en: "You must slow down and look both ways, but a complete stop is not required if the barrier is open and no train is approaching. However, you must confirm safety before crossing.", exp_pt: "Você deve reduzir a velocidade e olhar ambos os lados, mas a parada completa não é necessária se a barreira estiver aberta e não houver trem se aproximando. No entanto, deve confirmar a segurança antes de cruzar.", tricky: true, pattern: "stop-vs-slowdown" },
    { en: "If a railroad crossing barrier starts lowering while you are already on the tracks, you must immediately stop your vehicle.", pt: "Se a barreira de uma passagem de nível começar a descer enquanto você está nos trilhos, você deve parar o veículo imediatamente.", answer: "false", exp_en: "If you are already on the tracks when the barrier starts lowering, you must accelerate and clear the crossing immediately, not stop. Stopping on the tracks is extremely dangerous.", exp_pt: "Se você já está nos trilhos quando a barreira começa a descer, você deve acelerar e sair da passagem imediatamente, não parar. Parar nos trilhos é extremamente perigoso.", tricky: true, pattern: "stop-vs-accelerate" },
    { en: "You must not enter a railroad crossing if there is not enough space on the other side for your vehicle.", pt: "Você não deve entrar em uma passagem de nível se não houver espaço suficiente do outro lado para seu veículo.", answer: "true", exp_en: "You must not enter a railroad crossing unless there is sufficient space beyond it for your vehicle. This prevents becoming stranded on the tracks.", exp_pt: "Você não deve entrar em uma passagem de nível a menos que haja espaço suficiente além dela para seu veículo. Isso evita ficar preso nos trilhos." },
  ],
  6: [ // intersections
    { en: "When turning left at an intersection, you must stay as close as practicable to the left edge of the roadway.", pt: "Ao virar à esquerda em uma interseção, você deve permanecer o mais próximo possível da borda esquerda da via.", answer: "true", exp_en: "When turning left, you must approach as close as practicable to the left edge of the roadway and complete the turn along the left side.", exp_pt: "Ao virar à esquerda, você deve se aproximar o mais possível da borda esquerda da via e completar a curva pelo lado esquerdo." },
    { en: "When turning right at an intersection, you should turn from the rightmost lane and cut across oncoming traffic.", pt: "Ao virar à direita em uma interseção, você deve virar da pista mais à direita e cortar o tráfego contrário.", answer: "false", exp_en: "When turning right in Japan (left-hand traffic), you approach from the right side of the road but must wait for oncoming traffic to clear before turning. You do not 'cut across' recklessly.", exp_pt: "Ao virar à direita no Japão (tráfego mão esquerda), você se aproxima pelo lado direito da via mas deve esperar o tráfego contrário liberar antes de virar. Você não deve 'cortar' de forma imprudente." },
    { en: "At a flashing red signal, you must come to a complete stop before entering the intersection.", pt: "Em um sinal vermelho intermitente, você deve parar completamente antes de entrar na interseção.", answer: "true", exp_en: "A flashing red signal has the same meaning as a stop sign. You must come to a complete stop, yield to other traffic, then proceed when safe.", exp_pt: "Um sinal vermelho intermitente tem o mesmo significado de uma placa de pare. Você deve parar completamente, ceder passagem ao outro tráfego e prosseguir quando seguro." },
  ],
  7: [ // pedestrians-bicycles
    { en: "You must stop behind a pedestrian who is crossing at a crosswalk without a traffic signal.", pt: "Você deve parar atrás de um pedestre que está atravessando em uma faixa sem sinal de trânsito.", answer: "true", exp_en: "At an unsignalized crosswalk, vehicles must stop and yield to pedestrians. You must not pass or cut off a pedestrian who is crossing.", exp_pt: "Em uma faixa sem sinal, os veículos devem parar e ceder passagem aos pedestres. Você não deve ultrapassar ou cortar um pedestre que está atravessando." },
    { en: "Bicycles are required to use the roadway and are prohibited from using sidewalks unless specially marked.", pt: "Bicicletas são obrigadas a usar a via e são proibidas de usar calçadas, salvo sinalização especial.", answer: "true", exp_en: "In Japan, bicycles are generally required to use the roadway. Sidewalk cycling is only permitted where specially designated by signs or road markings.", exp_pt: "No Japão, bicicletas são geralmente obrigadas a usar a via. Pedalar na calçada só é permitido onde especialmente designado por placas ou marcações." },
    { en: "You may honk your horn to warn pedestrians who are walking on the roadway.", pt: "Você pode buzinar para alertar pedestres que estão andando na via.", answer: "false", exp_en: "The horn should be used only to avoid danger, not as a general warning to pedestrians. Excessive honking is a violation.", exp_pt: "A buzina deve ser usada apenas para evitar perigo, não como aviso geral aos pedestres. Buzinar excessivamente é uma infração." },
  ],
  8: [ // parking-stopping
    { en: "Parking within 5 meters of a fire hydrant is prohibited.", pt: "Estacionar a menos de 5 metros de um hidrante é proibido.", answer: "true", exp_en: "Parking within 5 meters of a fire hydrant is prohibited to ensure emergency access. This is a standard regulation in Japan.", exp_pt: "Estacionar a menos de 5 metros de um hidrante é proibido para garantir acesso de emergência. Esta é uma regulamentação padrão no Japão." },
    { en: "You may stop temporarily on the side of an expressway to check your phone.", pt: "Você pode parar temporariamente no acostamento de uma rodovia para verificar o celular.", answer: "false", exp_en: "Stopping on an expressway shoulder for non-emergency purposes is prohibited. Phone use while driving is also illegal. Only stop for genuine emergencies.", exp_pt: "Parar no acostamento de uma rodovia para fins não emergenciais é proibido. Usar o celular enquanto dirige também é ilegal. Pare apenas para emergências reais." },
    { en: "A 'no stopping' sign means you may park but must not stop the engine.", pt: "Uma placa de 'proibido parar' significa que você pode estacionar mas não deve desligar o motor.", answer: "false", exp_en: "A 'no stopping' sign prohibits both stopping and parking. You may not halt your vehicle there for any reason except emergencies.", exp_pt: "Uma placa de 'proibido parar' proíbe tanto parar quanto estacionar. Você não pode parar seu veículo lá por nenhum motivo, exceto emergências.", tricky: true, pattern: "parking-vs-stopping-confusion" },
  ],
  9: [ // emergency-vehicles
    { en: "When an emergency vehicle approaches with sirens, you must pull over to the left side of the road and stop.", pt: "Quando um veículo de emergência se aproxima com sirenes, você deve encostar à esquerda da via e parar.", answer: "true", exp_en: "In Japan (left-hand traffic), you must pull over to the LEFT side of the road and stop to allow emergency vehicles to pass on your right.", exp_pt: "No Japão (tráfego mão esquerda), você deve encostar à ESQUERDA da via e parar para permitir que veículos de emergência passem à sua direita." },
    { en: "Emergency vehicles are exempt from all traffic signals and signs at all times.", pt: "Veículos de emergência estão isentos de todos os sinais e placas de trânsito em todos os momentos.", answer: "false", exp_en: "Emergency vehicles responding to calls have certain exemptions but must still exercise due care. They are not exempt from all rules at all times.", exp_pt: "Veículos de emergência em chamadas têm certas isenções mas ainda devem ter o devido cuidado. Não estão isentos de todas as regras em todos os momentos." },
  ],
  10: [ // vehicle-inspection
    { en: "A vehicle must pass periodic inspection (shaken) every year for private passenger cars.", pt: "Um veículo deve passar por inspeção periódica (shaken) todos os anos para carros particulares.", answer: "false", exp_en: "For private passenger cars in Japan, the shaken (periodic inspection) is required every 2 years for newer cars, not annually. The first inspection is at 3 years.", exp_pt: "Para carros particulares no Japão, o shaken (inspeção periódica) é necessário a cada 2 anos para carros mais novos, não anualmente. A primeira inspeção é aos 3 anos.", tricky: true, pattern: "frequency-confusion" },
    { en: "Driving with an expired shaken certificate is a traffic violation.", pt: "Dirigir com o certificado shaken vencido é uma infração de trânsito.", answer: "true", exp_en: "Driving without a valid shaken is a violation. The shaken certifies that the vehicle meets safety and emissions standards.", exp_pt: "Dirigir sem shaken válido é uma infração. O shaken certifica que o veículo atende aos padrões de segurança e emissões." },
  ],
  11: [ // driver-obligations
    { en: "You must carry your driver's license at all times while driving.", pt: "Você deve portar sua carteira de motorista em todos os momentos enquanto dirige.", answer: "true", exp_en: "In Japan, you must carry your driver's license whenever driving. Failure to carry it is a violation punishable by fine.", exp_pt: "No Japão, você deve portar sua carteira de motorista sempre que dirigir. Não portá-la é uma infração punível com multa." },
    { en: "You are required to report any change of address to the police within 14 days.", pt: "Você é obrigado a comunicar qualquer mudança de endereço à polícia dentro de 14 dias.", answer: "true", exp_en: "When you change your address, you must report it to the police (driver's license center) within 14 days to update your license records.", exp_pt: "Quando você muda de endereço, deve comunicar à polícia (centro de carteiras) dentro de 14 dias para atualizar seus registros." },
    { en: "It is the driver's responsibility to ensure all passengers wear seat belts, including rear-seat passengers.", pt: "É responsabilidade do motorista garantir que todos os passageiros usem cinto, incluindo passageiros do banco traseiro.", answer: "true", exp_en: "The driver is responsible for ensuring all passengers wear seat belts. Rear-seat belt use has been mandatory in Japan since 2008.", exp_pt: "O motorista é responsável por garantir que todos os passageiros usem cinto. O uso de cinto no banco traseiro é obrigatório no Japão desde 2008." },
  ],
  12: [ // license-regulations
    { en: "A provisional license holder must display a 'beginner driver' mark on their vehicle.", pt: "Um portador de licença provisória deve exibir a marca 'motorista iniciante' no veículo.", answer: "true", exp_en: "Beginner drivers (within the first year after obtaining a license) must display the 'wakaba' (green leaf) mark on their vehicle.", exp_pt: "Motoristas iniciantes (no primeiro ano após obter a carteira) devem exibir a marca 'wakaba' (folha verde) no veículo." },
    { en: "A driver's license expires on the holder's birthday every 3 years for ordinary licenses.", pt: "A carteira de motorista expira no aniversário do titular a cada 3 anos para carteiras comuns.", answer: "false", exp_en: "In Japan, ordinary driver's licenses are valid until the holder's 3rd birthday after issuance (typically 3 years), but the exact period can vary. The renewal notice is sent before expiration.", exp_pt: "No Japão, carteiras de motorista comuns são válidas até o 3º aniversário do titular após a emissão (tipicamente 3 anos), mas o período exato pode variar. O aviso de renovação é enviado antes do vencimento." },
    { en: "Driving with a license that has been suspended is treated the same as driving without a license.", pt: "Dirigir com a carteira suspensa é tratado igual a dirigir sem carteira.", answer: "true", exp_en: "Driving with a suspended license is treated as unlicensed driving (mumenkyo unten), which is a serious criminal offense in Japan.", exp_pt: "Dirigir com a carteira suspensa é tratado como direção sem carteira (mumenkyo unten), que é um crime grave no Japão." },
  ],
  13: [ // traffic-violations
    { en: "Running a red light results in a fine and demerit points on your license.", pt: "Avançar no sinal vermelho resulta em multa e pontos na carteira.", answer: "true", exp_en: "Running a red light is a violation that results in a fine and demerit points. Accumulating points can lead to license suspension or revocation.", exp_pt: "Avançar no sinal vermelho é uma infração que resulta em multa e pontos. Acumular pontos pode levar à suspensão ou cassação da carteira." },
    { en: "A first-time speeding violation of less than 15 km/h over the limit results in license revocation.", pt: "Uma primeira infração de velocidade de menos de 15 km/h acima do limite resulta em cassação da carteira.", answer: "false", exp_en: "A first-time speeding violation of less than 15 km/h over the limit results in a small fine and 1 demerit point, not revocation. Revocation requires serious or repeated offenses.", exp_pt: "Uma primeira infração de velocidade de menos de 15 km/h acima do limite resulta em multa pequena e 1 ponto, não cassação. Cassação requer infrações graves ou repetidas." },
  ],
  14: [ // expressway-driving
    { en: "The maximum speed limit on expressways in Japan is 100 km/h for ordinary passenger cars.", pt: "O limite máximo de velocidade em rodovias no Japão é 100 km/h para carros de passejo comuns.", answer: "false", exp_en: "The maximum speed limit on expressways in Japan is 120 km/h for ordinary passenger cars on designated sections, with 100 km/h as the default on most expressways.", exp_pt: "O limite máximo de velocidade em rodovias no Japão é 120 km/h para carros de passejo comuns em trechos designados, com 100 km/h como padrão na maioria das rodovias.", tricky: true, pattern: "limit-value-confusion" },
    { en: "You must maintain a minimum speed of 50 km/h on expressways unless traffic conditions prevent it.", pt: "Você deve manter uma velocidade mínima de 50 km/h em rodovias, salvo condições de tráfego que o impeçam.", answer: "true", exp_en: "On expressways, the minimum speed is 50 km/h. Driving significantly below this without reason (e.g., traffic) is dangerous and prohibited.", exp_pt: "Em rodovias, a velocidade mínima é 50 km/h. Dirigir significativamente abaixo disso sem motivo (ex: tráfego) é perigoso e proibido." },
    { en: "Making a U-turn on an expressway is permitted at designated turnaround points only.", pt: "Fazer retorno em uma rodovia é permitido apenas em pontos de retorno designados.", answer: "true", exp_en: "U-turns on expressways are only permitted at designated turnaround points. Making a U-turn at other locations is extremely dangerous and prohibited.", exp_pt: "Retornos em rodovias só são permitidos em pontos de retorno designados. Fazer retorno em outros locais é extremamente perigoso e proibido." },
  ],
  15: [ // night-driving
    { en: "You must use high beams headlights whenever driving on an unlit road at night.", pt: "Você deve usar farol alto sempre que dirigir em via sem iluminação à noite.", answer: "false", exp_en: "High beams should be used on unlit roads but must be switched to low beams when approaching oncoming traffic or following another vehicle. Using high beams blindly is dangerous.", exp_pt: "O farol alto deve ser usado em vias sem iluminação mas deve ser trocado para farol baixo ao se aproximar de tráfego contrário ou seguir outro veículo. Usar farol alto cegamente é perigoso." },
    { en: "It is recommended to reduce speed at night because visibility is reduced compared to daytime.", pt: "É recomendado reduzir a velocidade à noite porque a visibilidade é reduzida comparada ao dia.", answer: "true", exp_en: "Night driving reduces visibility significantly. You should reduce speed to ensure you can stop within the distance illuminated by your headlights.", exp_pt: "Dirigir à noite reduz significativamente a visibilidade. Você deve reduzir a velocidade para garantir que possa parar dentro da distância iluminada pelos faróis." },
  ],
  16: [ // adverse-weather
    { en: "In heavy rain, you should turn on hazard lights to warn other drivers while continuing at normal speed.", pt: "Em chuva forte, você deve ligar as luzes de perigo para alertar outros motoristas enquanto continua em velocidade normal.", answer: "false", exp_en: "In heavy rain, you should reduce speed and turn on headlights or fog lights. Hazard lights should not be used while moving in normal traffic; they are for stopped vehicles.", exp_pt: "Em chuva forte, você deve reduzir a velocidade e ligar os faróis ou luzes de neblina. As luzes de perigo não devem ser usadas enquanto se move em tráfego normal; são para veículos parados.", tricky: true, pattern: "hazard-light-misuse" },
    { en: "When driving in fog, you should use low beam headlights, not high beams.", pt: "Ao dirigir na neblina, você deve usar farol baixo, não farol alto.", answer: "true", exp_en: "High beams in fog reflect off the water particles, reducing visibility. Low beams or fog lights provide better illumination in foggy conditions.", exp_pt: "Faróis altos na neblina refletem nas partículas de água, reduzindo a visibilidade. Faróis baixos ou luzes de neblina fornecem melhor iluminação em condições de neblina." },
    { en: "On snowy or icy roads, you should brake suddenly to test the road surface grip.", pt: "Em vias com neve ou gelo, você deve frear bruscamente para testar a aderência da superfície.", answer: "false", exp_en: "Sudden braking on snowy or icy roads can cause loss of control. You should brake gently and gradually, using engine braking where possible.", exp_pt: "Frear bruscamente em vias com neve ou gelo pode causar perda de controle. Você deve frear suave e gradualmente, usando o freio do motor quando possível." },
  ],
  17: [ // vehicle-loading
    { en: "The maximum vehicle width for ordinary passenger cars in Japan is 2.5 meters.", pt: "A largura máxima para carros de passejo comuns no Japão é 2,5 metros.", answer: "false", exp_en: "The maximum width for ordinary vehicles in Japan is 1.9 meters (excluding mirrors). This is narrower than international standards, reflecting Japan's narrow roads.", exp_pt: "A largura máxima para veículos comuns no Japão é 1,9 metro (excluindo espelhos). Isso é mais estreito que os padrões internacionais, refletindo as vias estreitas do Japão.", tricky: true, pattern: "dimension-confusion" },
    { en: "Cargo extending beyond the rear of the vehicle by more than 10% of the vehicle length requires a warning flag.", pt: "Carga que se estende além da traseira do veículo em mais de 10% do comprimento do veículo requer uma bandeira de aviso.", answer: "true", exp_en: "When cargo extends beyond the rear by more than 10% of the vehicle length, a red flag or warning marker must be displayed at night and during the day.", exp_pt: "Quando a carga se estende além da traseira em mais de 10% do comprimento do veículo, uma bandeira vermelha ou marcador de aviso deve ser exibido à noite e durante o dia." },
  ],
  18: [ // towing
    { en: "An ordinary license holder may tow a trailer weighing up to 750 kg.", pt: "Um portador de carteira comum pode rebocar um trailer pesando até 750 kg.", answer: "true", exp_en: "An ordinary (Class 1) license allows towing a trailer with a maximum laden weight of 750 kg. Heavier trailers require a special trailer license.", exp_pt: "Uma carteira comum (Classe 1) permite rebocar um trailer com peso máximo de 750 kg. Trailers mais pesados requerem uma carteira especial de reboque." },
    { en: "When towing, the safety chain is optional if the hitch coupling is properly connected.", pt: "Ao rebocar, a corrente de segurança é opcional se o acoplamento estiver corretamente conectado.", answer: "false", exp_en: "A safety chain or secondary coupling device is mandatory when towing. It prevents the trailer from detaching completely if the primary hitch fails.", exp_pt: "Uma corrente de segurança ou dispositivo de acoplamento secundário é obrigatório ao rebocar. Impede que o trailer se desacople completamente se a hitch principal falhar." },
  ],
  19: [ // seat-belts-child-seats
    { en: "Children under 6 years old must use a child restraint system (child seat).", pt: "Crianças menores de 6 anos devem usar um sistema de retenção infantil (cadeirinha).", answer: "true", exp_en: "In Japan, children under 6 must use an age/size-appropriate child restraint system. The driver is responsible for ensuring compliance.", exp_pt: "No Japão, crianças menores de 6 anos devem usar um sistema de retenção infantil apropriado para idade/tamanho. O motorista é responsável por garantir o cumprimento." },
    { en: "Pregnant women are exempt from the seat belt requirement for safety reasons.", pt: "Mulheres grávidas estão isentas da exigência de cinto de segurança por motivos de segurança.", answer: "false", exp_en: "Pregnant women are not exempt from seat belt requirements. They should wear the belt with the lap belt positioned below the abdomen for safety.", exp_pt: "Mulheres grávidas não estão isentas da exigência de cinto. Devem usar o cinto com a faixa abdominal posicionada abaixo da barriga para segurança." },
  ],
  20: [ // mobile-phone-use
    { en: "Using a mobile phone while driving is prohibited even when the vehicle is stopped at a red light.", pt: "Usar celular enquanto dirige é proibido mesmo quando o veículo está parado no sinal vermelho.", answer: "true", exp_en: "Using a mobile phone while driving is prohibited at all times, including when stopped at a red light. The vehicle is still considered 'in traffic' when stopped at a signal.", exp_pt: "Usar celular enquanto dirige é proibido em todos os momentos, incluindo quando parado no sinal vermelho. O veículo ainda é considerado 'no trânsito' quando parado no sinal." },
    { en: "Hands-free phone use with a Bluetooth headset is permitted while driving.", pt: "O uso de telefone viva-voz com fone Bluetooth é permitido enquanto dirige.", answer: "false", exp_en: "In Japan, even hands-free phone use while driving is discouraged and can be penalized if it causes dangerous driving. Holding the phone is strictly prohibited.", exp_pt: "No Japão, mesmo o uso viva-voz enquanto dirige é desencorajado e pode ser penalizado se causar direção perigosa. Segurar o telefone é estritamente proibido.", tricky: true, pattern: "hands-free-confusion" },
  ],
  21: [ // drinking-driving
    { en: "Driving with a blood alcohol concentration of 0.03% or higher is punishable in Japan.", pt: "Dirigir com concentração de álcool no sangue de 0,03% ou mais é punível no Japão.", answer: "true", exp_en: "Japan has a strict zero-tolerance policy for drinking and driving. Any detectable alcohol level can result in punishment, with BAC of 0.03% or higher leading to severe penalties.", exp_pt: "O Japão tem uma política rigorosa de tolerância zero para álcool e direção. Qualquer nível detectável de álcool pode resultar em punição, com BAC de 0,03% ou mais levando a penalidades severas." },
    { en: "Providing alcohol to someone who then drives is not punishable under Japanese law.", pt: "Fornecer álcool a alguém que depois dirige não é punível pela lei japonesa.", answer: "false", exp_en: "In Japan, providing alcohol to someone who then drives, or allowing an intoxicated person to drive your vehicle, is a punishable offense. This includes passengers and bar owners.", exp_pt: "No Japão, fornecer álcool a alguém que depois dirige, ou permitir que uma pessoa intoxicada dirija seu veículo, é uma infração punível. Isso inclui passageiros e donos de bar." },
    { en: "A first-time DUI offense can result in imprisonment of up to 5 years.", pt: "Uma primeira infração de DUI pode resultar em prisão de até 5 anos.", answer: "true", exp_en: "Under Japanese law, driving under the influence (DUI) can result in up to 5 years imprisonment and a fine of up to 1 million yen, even for a first offense.", exp_pt: "Sob a lei japonesa, dirigir sob efeito (DUI) pode resultar em até 5 anos de prisão e multa de até 1 milhão de ienes, mesmo em uma primeira infração." },
  ],
  22: [ // first-aid-accidents
    { en: "If you are the first to arrive at an accident scene, you must stop and render aid.", pt: "Se você for o primeiro a chegar ao local de um acidente, deve parar e prestar socorro.", answer: "true", exp_en: "In Japan, you have a duty to stop and assist at an accident scene. Failing to do so is a violation (hit-and-run / tenki bousou).", exp_pt: "No Japão, você tem o dever de parar e auxiliar no local de um acidente. Não fazer isso é uma infração (fuga / tenki bousou)." },
    { en: "When calling emergency services (110 or 119), you should hang up immediately after reporting to keep the line free.", pt: "Ao ligar para serviços de emergência (110 ou 119), você deve desligar imediatamente após relatar para manter a linha livre.", answer: "false", exp_en: "After calling emergency services, you should stay on the line until the operator tells you to hang up. They may need additional information or give you instructions.", exp_pt: "Após ligar para serviços de emergência, você deve permanecer na linha até o operador dizer para desligar. Eles podem precisar de informações adicionais ou dar instruções." },
    { en: "If an injured person is unconscious but breathing, you should place them in the recovery position.", pt: "Se uma pessoa ferida estiver inconsciente mas respirando, você deve colocá-la na posição lateral de segurança.", answer: "true", exp_en: "The recovery position helps maintain an open airway for an unconscious but breathing person, preventing aspiration. This is standard first aid practice.", exp_pt: "A posição lateral de segurança ajuda a manter as vias aéreas abertas para uma pessoa inconsciente mas respirando, prevenindo aspiração. Esta é a prática padrão de primeiros socorros." },
  ],
};

// ─── Generate mock questions ───────────────────────────────────────────────

function generateMockQuestions(): QuestionListItem[] {
  const questions: QuestionListItem[] = [];
  let qid = 1;

  for (const theme of mockThemes) {
    const prompts = PROMPTS[theme.id] ?? [];
    for (const p of prompts) {
      questions.push({
        id: qid,
        theme_id: theme.id,
        prompt_en: p.en,
        prompt_pt: p.pt,
        tricky: p.tricky ?? false,
        tricky_pattern: p.pattern ?? null,
        difficulty: p.difficulty ?? 0.5,
        translations_status: "complete",
      });
      qid++;
    }
  }

  return questions;
}

function generateMockQuestionDetails(): Map<number, QuestionDetail> {
  const details = new Map<number, QuestionDetail>();
  let qid = 1;

  for (const theme of mockThemes) {
    const prompts = PROMPTS[theme.id] ?? [];
    for (const p of prompts) {
      details.set(qid, {
        id: qid,
        theme_id: theme.id,
        prompt_en: p.en,
        prompt_pt: p.pt,
        tricky: p.tricky ?? false,
        tricky_pattern: p.pattern ?? null,
        difficulty: p.difficulty ?? 0.5,
        translations_status: "complete",
        answer_en: p.answer,
        answer_pt: p.answer,
        explanation_en: p.exp_en,
        explanation_pt: p.exp_pt,
      });
      qid++;
    }
  }

  return details;
}

// ─── Exported mock data ─────────────────────────────────────────────────────

export const mockQuestionList: QuestionListItem[] = generateMockQuestions();
export const mockQuestionDetails: Map<number, QuestionDetail> =
  generateMockQuestionDetails();

/** Count questions per theme from the mock list. */
export function mockCountByTheme(themeId: number): number {
  return mockQuestionList.filter((q) => q.theme_id === themeId).length;
}

// ─── Mock Test Attempt Management ──────────────────────────────────────────

import type {
  AttemptStartIn,
  AttemptSubmitIn,
  AttemptResultOut,
  AttemptAnswerOut,
} from "@/types";

export interface MockTestStartResponse {
  attempt_id: number;
  questions: QuestionListItem[];
  time_limit_seconds: number;
}

export interface MockTestTimeoutResponse {
  remaining_seconds: number;
  timed_out: boolean;
}

/** In-memory store for active mock test attempts. */
interface MockAttempt {
  attempt_id: number;
  questions: QuestionListItem[];
  time_limit_seconds: number;
  started_at: number;
  difficulty: number;
}

const mockAttempts = new Map<number, MockAttempt>();
let nextAttemptId = 1;

/** Deterministic shuffle using a simple LCG. */
function seededShuffle<T>(arr: T[], seed: number): T[] {
  const result = [...arr];
  let s = seed || 1;
  for (let i = result.length - 1; i > 0; i--) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const j = s % (i + 1);
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

/** Start a mock test attempt — generates 50 questions from the pool. */
export function mockStartAttempt(
  payload: AttemptStartIn,
): MockTestStartResponse {
  const attemptId = nextAttemptId++;
  const seed = payload.seed ?? attemptId * 1000;

  // Cycle through the question pool to get 50 questions
  const pool = seededShuffle(mockQuestionList, seed);
  const questions: QuestionListItem[] = [];
  let idx = 0;
  while (questions.length < payload.question_count) {
    const q = pool[idx % pool.length];
    // Avoid duplicates — if pool is large enough
    if (!questions.some((qq) => qq.id === q.id)) {
      questions.push({ ...q });
    }
    idx++;
    // Safety: if pool is smaller than question_count, allow duplicates
    if (idx > pool.length * 3) {
      questions.push({ ...pool[idx % pool.length], id: -(idx) });
      idx++;
    }
  }

  mockAttempts.set(attemptId, {
    attempt_id: attemptId,
    questions,
    time_limit_seconds: payload.time_limit_seconds,
    started_at: Date.now(),
    difficulty: payload.tricky_ratio,
  });

  return {
    attempt_id: attemptId,
    questions,
    time_limit_seconds: payload.time_limit_seconds,
  };
}

/** Submit a mock test attempt — calculates results. */
export function mockSubmitAttempt(
  attemptId: number,
  payload: AttemptSubmitIn,
): AttemptResultOut | null {
  const attempt = mockAttempts.get(attemptId);
  if (!attempt) return null;

  const answers: AttemptAnswerOut[] = attempt.questions.map((q) => {
    const userAnswerEntry = payload.answers.find(
      (a) => a.question_id === q.id,
    );
    const userAnswer = (userAnswerEntry?.user_answer ?? "false") as "true" | "false";
    const detail = mockQuestionDetails.get(q.id);
    const correctAnswer = (detail?.answer_en ?? "true") as "true" | "false";
    const isCorrect = userAnswer === correctAnswer;

    return {
      question_id: q.id,
      is_correct: isCorrect,
      user_answer: userAnswer,
      correct_answer: correctAnswer,
      explanation_en: detail?.explanation_en ?? "",
      explanation_pt: detail?.explanation_pt ?? "",
    };
  });

  const score = answers.filter((a) => a.is_correct).length;
  const maxScore = attempt.questions.length;
  const boundaryScore = Math.ceil(maxScore * 0.9); // 90% = 45/50
  const passed = score >= boundaryScore;

  return {
    attempt_id: attemptId,
    score,
    max_score: maxScore,
    passed,
    tricky_ratio_actual: attempt.difficulty,
    boundary_score: boundaryScore,
    answers,
  };
}

/** Check timeout status for a mock test attempt. */
export function mockGetTimeout(
  attemptId: number,
): MockTestTimeoutResponse | null {
  const attempt = mockAttempts.get(attemptId);
  if (!attempt) return null;

  const elapsed = Math.floor((Date.now() - attempt.started_at) / 1000);
  const remaining = Math.max(0, attempt.time_limit_seconds - elapsed);
  const timedOut = remaining <= 0;

  return {
    remaining_seconds: remaining,
    timed_out: timedOut,
  };
}

/** Get the correct answers for a mock attempt (test helper). */
export function mockGetCorrectAnswers(
  attemptId: number,
): Record<number, "true" | "false"> | null {
  const attempt = mockAttempts.get(attemptId);
  if (!attempt) return null;

  const result: Record<number, "true" | "false"> = {};
  for (const q of attempt.questions) {
    const detail = mockQuestionDetails.get(q.id);
    if (detail) {
      result[q.id] = detail.answer_en as "true" | "false";
    }
  }
  return result;
}