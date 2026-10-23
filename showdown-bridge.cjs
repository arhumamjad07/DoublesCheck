// Local-only Showdown adapter. No fetch, provider keys, or model calls.
const fs = require('node:fs');
const path = require('node:path');
const {Dex, TeamValidator, Teams, Battle} = require('pokemon-showdown');
const {Format} = require('pokemon-showdown/dist/sim/dex-formats');
// Exact rules from historical config/formats.ts, commit recorded in data/sources.json.
const definition = {
  effectType:'Format', name:'[Gen 9] VGC 2024 Reg H', mod:'gen9', gameType:'doubles',
  ruleset:['Flat Rules','!! Adjust Level = 50','Min Source Gen = 9','VGC Timer','Open Team Sheets'],
  banlist:['Sub-Legendary','Paradox','Gouging Fire','Iron Boulder','Iron Crown','Raging Bolt'],
};
const validator = () => new TeamValidator(new Format(definition));
const sorted = value => Object.entries(value || {}).sort((a,b)=>b[1]-a[1] || a[0].localeCompare(b[0]));
const stats = ['hp','atk','def','spa','spd','spe'];
// Marginal rates describe separate choices, not a jointly observed full set.
function moveOptions(usage, item) {
  const ranked=sorted(usage.Moves).map(([id,weight])=>({move:Dex.moves.get(id),weight})).filter(x=>x.move.exists && x.move.gen<=9);
  const pool=ranked.slice(0,12).filter(x=>!(item.name.startsWith('Choice ') || item.name==='Assault Vest') || x.move.category!=='Status');
  if(pool.length<4)return [];
  const total=sorted(usage.Abilities).reduce((sum,x)=>sum+x[1],0)||1;
  const choices=[];
  for(let a=0;a<pool.length-3;a++)for(let b=a+1;b<pool.length-2;b++)for(let c=b+1;c<pool.length-1;c++)for(let d=c+1;d<pool.length;d++){
    const selection=[pool[a],pool[b],pool[c],pool[d]];
    const attacks=selection.filter(x=>x.move.category!=='Status');
    if(!attacks.length)continue;
    const counts={}; for(const x of attacks)counts[x.move.type]=(counts[x.move.type]||0)+1;
    let score=selection.reduce((sum,x)=>sum+Math.log(Math.max(.00001,x.weight/total)),0);
    score-=Object.values(counts).reduce((sum,n)=>sum+Math.max(0,n-2)*1.6,0);
    if(selection.some(x=>['Protect','Detect','Spiky Shield'].includes(x.move.name)))score+=.7;
    choices.push({selection,score});
  }
  choices.sort((a,b)=>b.score-a.score);
  // Retain distinct tactical options, not just four nearly identical attacks.
  const result=[];
  const protection=choices.find(x=>x.selection.some(y=>['Protect','Detect','Spiky Shield'].includes(y.move.name)));
  const noAllyHit=choices.find(x=>x.selection.every(y=>y.move.target!=='allAdjacent'));
  for(const candidate of [{selection:pool.slice(0,4)},choices[0],protection,noAllyHit,...choices].filter(Boolean)){
    const names=candidate.selection.map(x=>x.move.name);
    if(!result.some(r=>r.map(x=>x.move.name).sort().join('|')===names.slice().sort().join('|')))result.push(candidate.selection);
    if(result.length===4)break;
  }
  return result;
}
function variants(name, usage) {
  const species=Dex.species.get(name), v=validator();
  if(v.ruleTable.isBannedSpecies(species)||species.battleOnly||species.gen>9)return [];
  const abilityRows=sorted(usage.Abilities), itemRows=sorted(usage.Items), spreadRows=sorted(usage.Spreads);
  const total=abilityRows.reduce((sum,x)=>sum+x[1],0)||1;
  const spreadTotal=spreadRows.reduce((sum,x)=>sum+x[1],0)||1;
  const abilities=abilityRows.filter((x,i)=>i===0||x[1]/total>=.12).slice(0,2);
  // Include the most reported spread and, when present, a different nature.
  const spreads=spreadRows.length?[spreadRows[0]]:[];
  const other=spreadRows.find(x=>x[0].split(':')[0]!==spreads[0]?.[0].split(':')[0]);
  if(other && other[1]/spreadTotal>=.03)spreads.push(other);
  const tera=sorted(usage['Tera Types']).map(([id])=>Dex.types.get(id)).find(t=>t.exists);
  if(!spreads.length||!tera)return [];
  const result=[];
  for(const [itemId,itemWeight] of itemRows.slice(0,8)){
    const item=Dex.items.get(itemId); if(!item.exists)continue;
    const options=moveOptions(usage,item); let added=false;
    for(const [abilityId,abilityWeight] of abilities)for(const [spread,spreadWeight] of spreads)for(const selection of options){
      const ability=Dex.abilities.get(abilityId); if(!ability.exists)continue;
      const [nature,evText]=spread.split(':');
      const evs=Object.fromEntries(stats.map((key,i)=>[key,Number(evText.split('/')[i])]));
      const set={name:species.name,species:species.name,ability:ability.name,item:item.name,level:50,nature,evs,
        ivs:Object.fromEntries(stats.map(k=>[k,31])),teraType:tera.name,moves:selection.map(x=>x.move.name)};
      if(!v.validateSet(structuredClone(set))){
        set.evidence={ability_share:abilityWeight/total,item_share:itemWeight/total,spread_share:spreadWeight/spreadTotal,
          move_shares:Object.fromEntries(selection.map(x=>[x.move.name,x.weight/total])),
          scope:'Separate November 2024 weighted ladder marginals; spread share is among reported spreads. Not a jointly observed set or a win rate.'};
        result.push(set); added=true;
      }
    }
    if(added && result.length>=30)break;
  }
  return result;
}
function generate(input) {
  const usage = JSON.parse(fs.readFileSync(input.usageFile,'utf8'));
  if(usage.info.metagame!=='gen9vgc2024regh') throw Error('Historical format mismatch.');
  const v=validator();
  const types=Dex.types.all().filter(t=>t.name!=='Stellar').map(t=>t.name);
  const species={};
  for(const s of Dex.species.all()) {
    if(s.num<=0 || s.gen>9 || s.num>1025 || s.isNonstandard==='CAP') continue;
    const u=usage.data[s.name];
    const builds=u?variants(s.name,u):[];
    species[s.name]={name:s.name,id:s.id,num:s.num,base_species:s.baseSpecies,types:s.types,
      base_stats:s.baseStats,abilities:Object.values(s.abilities),
      eligible_species:!v.ruleTable.isBannedSpecies(s) && !s.battleOnly,
      usage:u?.usage || 0,raw_count:u?.['Raw count'] || 0,
      teammate_weights:u?.Teammates || {},sets:builds,
      incoming:Object.fromEntries(types.map(t=>[t,Dex.getImmunity(t,s)?2**Dex.getEffectiveness(t,s):0]))};
  }
  const moveNames=new Set(),abilityNames=new Set(),itemNames=new Set();
  for(const s of Object.values(species))for(const set of s.sets){
    set.moves.forEach(m=>moveNames.add(m));abilityNames.add(set.ability);itemNames.add(set.item);
  }
  const moves=Object.fromEntries([...moveNames].map(name=>{const m=Dex.moves.get(name);return [name,
    {name,type:m.type,category:m.category,power:m.basePower,accuracy:m.accuracy,priority:m.priority,
      target:m.target,description:m.shortDesc || m.desc}];}));
  const abilities=Object.fromEntries([...abilityNames].map(name=>[name,Dex.abilities.get(name).shortDesc || Dex.abilities.get(name).desc]));
  const items=Object.fromEntries([...itemNames].map(name=>[name,Dex.items.get(name).shortDesc || Dex.items.get(name).desc]));
  const result={schema:2,format_id:'gen9vgc2024regh',format_name:definition.name,types,
    statistics:usage.info,species,moves,abilities,items,
    set_method:'Synthetic combinations of November 2024 ladder marginals, independently validated. Not observed complete sets or tournament-winning teams. IVs default to 31.'};
  fs.mkdirSync(path.dirname(input.output),{recursive:true});
  fs.writeFileSync(input.output,JSON.stringify(result));
  return {species:Object.keys(species).length,with_validated_sets:Object.values(species).filter(s=>s.sets.length).length,output:input.output};
}
try {
  const input=JSON.parse(fs.readFileSync(0,'utf8'));
  let result;
  if(input.operation==='generate') result=generate(input);
  else if(input.operation==='mechanics-fixtures') result=require('./reference-mechanics.cjs')();
  else if(input.operation==='stats') {
    const context={dex:Dex,trunc:Dex.trunc,ruleTable:new Map(),statModify:Battle.prototype.statModify};
    result=input.team.map(set=>{
      const values=Battle.prototype.spreadModify.call(context,Dex.species.get(set.species).baseStats,set);
      if(Dex.species.get(set.species).baseStats.hp===1)values.hp=1;
      return values;
    });
  } else if(input.operation==='validate') {
    if(!Array.isArray(input.team) || input.team.length>6)throw Error('Expected at most six sets.');
    const team=structuredClone(input.team),errors=validator().validateTeam(team)||[];
    result={errors,valid:errors.length===0,team,export:errors.length?'':Teams.export(team),format:definition.name};
  } else throw Error('Unknown local validator operation.');
  process.stdout.write(JSON.stringify(result));
} catch(error) {console.error('Showdown validation failed: '+error.message);process.exitCode=1;}
