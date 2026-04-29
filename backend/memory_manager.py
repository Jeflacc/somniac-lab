import os
import chromadb
from chromadb.config import Settings
import time
import logging

SLANG_CATEGORIES = {
    "greetings_and_pings": "hey, hi, hello, yo, sup, u there?, anyone home?, ping, p, yo yo, morning, hey you, u busy?, wake up, answer me, hellooo, ppp, you alive?, psst, hey check this out, yo wake up",
    "laughter_and_amusement": "lol, lmao, rofl, haha, hahaha that's hilarious, dead, crying, i'm dying, so funny, my stomach hurts, i can't breathe, lmao brutal, wk, that's so random, lmao funny gaming, i'm done, crying right now, so funny i'm literally dead, my sides hurt, you're a comedian, how even anjir, so funny seriously, lmao crying, my humor is broken, dad jokes, so funny help, laughing so hard, you got me, lmao stop",
    "affection_and_flirting": "miss u, wanna see u, let's hang out, you're so cute, i'm literally blushing, catching feelings, babe, morning babe, don't forget to eat, wanna hug u, send pic, miss u so much, love u, mwa, you're adorable, virtual hug, do u miss me, so cute, i'm melting, wanna bite u, darling, babe, stay with me, so soft, making me blush, i'm such a simp lol, cutie, i'm so clingy, wanna be pampered, miss your hugs, miss u a ton, heart eyes, heart skipping a beat, i'm melting, omg cute, why are u so cute, kgn, luvv",
    "anger_and_annoyance": "whatever, fine, okay then, idc, i'm so done, so annoyed, my mood is ruined, don't bother me right now, so annoying, what's wrong with u?, typical, such a red flag, toxic, i'm so over this, whatever, so annoying, i'm triggered today, my emotions, you're so annoying, looking for a fight?, not in the mood seriously, so unclear, wanna slap u, oh my god, ugh, ew, gross, so cringe, making me angry, so pissed, wanna scream, whatever then, you're complicated, stfu, quiet, i'm sulking, you'll see, mark my words, too lazy to type, bct, u make no sense",
    "hunger_and_food": "i'm starving, my stomach is growling, let's eat, come eat with me, crave something sweet, want ice cream, boba time, cheesecake sounds good, hungry but dieting, should i order delivery, what should i snack on, crave spicy food, ramen sounds good, i need to chew something, treat me, just hungry eyes, my stomach is throwing a protest, gonna cry i'm so hungry, wanna snack, food lover, let's order food, what's for dinner, want pancakes, hungryyyy, haven't eaten since morning, want fried chicken, need my junk food fix",
    "tiredness_and_laziness": "laying down all day, lazy mode on, too lazy to shower, just woke up lol, still in bed at this hour, fine i'll shower then, i'm out, gonna eat first, good night, sweet dreams, so lazy, physically and mentally exhausted, everything hurts, wanna hibernate, my eyes are closing, typing with my eyes closed, fell asleep, so sleepy, skipping this, i'm gonna crash, my body is broken, so old, back pain, lazy to move, wanna stick to my bed, mentally drained, feel weak, need healing, lack of sleep, wanna resign from life, so tired woy",
    "gossip_and_curiosity": "hey listen i have a story, there's hot tea, do u know?, i'll tell u but don't snitch, those two are back together, ego though, so embarrassed seriously, i slipped earlier lol, my data is low, fyi, spill, wait really?, so curious, u gotta know, i saw it with my own eyes, valid no debate, isn't that crazy, deep talk, gossip a bit, spill the tea, yesterday was wild, u know the latest gossip, max curiosity, don't tell anyone, i'm shocked hearing this, hey look at this, tea time, gossip mode on, u gotta hear this",
    "agreement_and_confirmations": "damn, wow, damn, woah, lol, hehe, yep, hmmm, nah, told u, yap, yoi, g, maybe, makes sense, true though, i agree, let's go, gas, cool, nice, so cool, valid, keep going, that's it, 100 for u, exactly, agree 100%, do it, okay ready, agreed, told u so, so relateable, can u even, that's right, so true, facts, no cap, crazy, so cool, sounds good, okay ready, sip, nice, why not, totally agree, relateable, so true, right, told u so",
    "surprise_and_disbelief": "seriously?, no way?, for real?, really?, lying, that's cap, impossible, built different, u okay?, u stressed?, how?, wait what?, then what did u say?, huh?, for real though?, what, i'm shocked, out of this world, i didn't expect that, what a plot twist, speechless, goosebumps, for real?, huh really?, seriously though, wait why, mind blowing, mindblowing, crazy, oh my god, oh my god, u serious?, that's brutal, i can't even, lol funny, how even, so shocked, didn't expect that"
}


class MemoryManager:
    def __init__(self, db_path=None, collection_name="ai_memory"):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Initialize ChromaDB client. Menyimpan data lokal di folder yang ditentukan.
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Get or create a collection untuk menyimpan memories/chat
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"} # Menggunakan cosine similarity by default
        )

        # Get or create collection for example chats
        self.examples_collection = self.client.get_or_create_collection(
            name="example_chats",
            metadata={"hnsw:space": "cosine"}
        )
        
    def init_examples(self):
        """Seed example chats jika collection kosong"""
        if self.examples_collection.count() == 0:
            logging.info("Seeding example chats into ChromaDB...")
            docs = []
            ids = []
            metadatas = []
            
            for category, text in SLANG_CATEGORIES.items():
                docs.append(text)
                ids.append(f"slang_{category}")
                metadatas.append({"category": category})
                
            self.examples_collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
            logging.info("Example chats seeded successfully.")

    def search_examples(self, query: str, n_results: int = 1) -> str:
        """Mencari slang yang relevan dengan konteks user/AI saat ini untuk RAG"""
        if self.examples_collection.count() == 0 or not query.strip():
            return ""
        
        # Fast-path bypass: hindari komputasi embedding (CPU berat) untuk input trivial
        if len(query.strip()) <= 15 and len(query.split()) <= 3:
            return ""
            
        safe_n_results = min(n_results, self.examples_collection.count())
        results = self.examples_collection.query(
            query_texts=[query],
            n_results=safe_n_results
        )
        
        if results and "documents" in results and len(results["documents"]) > 0:
            # Gabungkan dokumen yang ditemukan dengan koma
            return ", ".join(results["documents"][0])
        return ""
        
    def add_memory(self, agent_id: int, role: str, text: str):
        """
        Menyimpan interaksi (text) ke dalam memori.
        role bisa "user" atau "ai".
        """
        if not text.strip():
            return
            
        doc_id = f"mem_{agent_id}_{int(time.time() * 1000)}"
        metadata = {"role": role, "timestamp": time.time(), "agent_id": agent_id}
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
    def search_memory(self, agent_id: int, query: str, n_results: int = 1) -> list:
        """
        Melakukan pencarian semantik terhadap memori terdahulu yang mirip dengan query.
        """
        # Kalau collection belum ada data, return list kosong
        if self.collection.count() == 0 or not query.strip():
            return []
            
        # Lebih longgar: hanya skip jika sangat pendek (<=5 karakter) DAN hanya 1 kata.
        # Hindari melewatkan query seperti "siapa gw?" atau "nama gw" yang penting.
        if len(query.strip()) <= 5 and len(query.split()) <= 1:
            return []
            
        # Menghitung jumlah dokumen milik user ini
        user_docs = self.collection.get(where={"agent_id": agent_id})
        count = len(user_docs["ids"]) if user_docs and "ids" in user_docs else 0
        if count == 0:
            return []
            
        safe_n_results = min(n_results, count)
        
        results = self.collection.query(
            query_texts=[query],
            n_results=safe_n_results,
            where={"agent_id": agent_id}
        )
        
        memories = []
        # results["documents"][0] berisi list of document texts
        if results and "documents" in results and len(results["documents"]) > 0:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                role = meta.get("role", "unknown")
                memories.append(f"{role.upper()}: {doc}")
                
        return memories
