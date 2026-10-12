scoreboard players set #force angel.story 0
gamemode adventure @a
clear @a minecraft:written_book
clear @a minecraft:paper
give @a minecraft:written_book[written_book_content={title:"Letter",author:"Gendo Ikari",pages:[{raw:"Come."}]}]
give @a minecraft:paper[custom_name={text:"Photograph",italic:false},max_stack_size=1,lore=[{text:"A woman, smiling. On the back:",italic:false,color:"gray"},{text:"If I'm late, ring me from the phone outside the station. M.K.",italic:true,color:"gray"}]]
scoreboard players set #step angel.story 8
function angel:story/s1/e8
