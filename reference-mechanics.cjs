// Independent simulator fixtures for the coaching arithmetic. No network or AI.
const {Battle} = require('pokemon-showdown');
const stats=['hp','atk','def','spa','spd','spe'];
function member(species,ability,item,nature,evs,moves=['Protect']) {
  return {species,ability,item,nature,level:50,evs:{hp:0,atk:0,def:0,spa:0,spd:0,spe:0,...evs},ivs:Object.fromEntries(stats.map(k=>[k,31])),moves};
}
function withBattle(team, inspect) {
  const battle=new Battle({formatid:'gen9doublescustomgame',seed:[1,2,3,4]});
  try {
    const other=[member('Garchomp','Rough Skin','Life Orb','Jolly'),member('Incineroar','Blaze','Safety Goggles','Adamant')];
    battle.setPlayer('p1',{name:'Fixture one',team});
    battle.setPlayer('p2',{name:'Fixture two',team:other});
    battle.makeChoices('team 12','team 12');
    return inspect(battle,battle.p1.active[0]);
  } finally {battle.destroy();}
}
function fixtures() {
  const helper=member('Clefairy','Friend Guard','Eviolite','Bold');
  const scarf=withBattle([member('Charizard','Blaze','Choice Scarf','Timid',{spa:252,spe:252,hp:4}),helper],(b,p)=>{
    const normal=p.getStat('spe');b.p1.addSideCondition('tailwind',p);const wind=p.getStat('spe');
    b.field.addPseudoWeather('trickroom',p);return {normal,wind,room_stat:p.getStat('spe')};
  });
  const chlorophyll=withBattle([member('Venusaur','Chlorophyll','Life Orb','Modest',{spa:252,spd:4,spe:252}),member('Torkoal','Drought','Charcoal','Quiet')],(b,p)=>{
    const sun=p.getStat('spe');b.field.clearWeather();return {sun,clear:p.getStat('spe')};
  });
  const seed=withBattle([member('Sneasler','Unburden','Psychic Seed','Jolly',{atk:252,spe:252,hp:4}),member('Indeedee-F','Psychic Surge','Safety Goggles','Bold')],(b,p)=>({speed:p.getStat('spe'),item:p.item,active:!!p.volatiles.unburden}));
  const sash=withBattle([member('Sneasler','Unburden','Focus Sash','Jolly',{atk:252,spe:252,hp:4}),helper],(b,p)=>({speed:p.getStat('spe'),active:!!p.volatiles.unburden}));
  const grounding=withBattle([member('Charizard','Blaze','Iron Ball','Timid'),helper],(b,p)=>p.isGrounded());
  return {scarf,chlorophyll,seed,sash,iron_ball_grounded:grounding};
}
module.exports=fixtures;
if(require.main===module)process.stdout.write(JSON.stringify(fixtures()));
