import os
import chromadb
from chromadb.config import Settings
import time
import logging

SLANG_CATEGORIES = {
    "greetings_and_pings": "ping, p dong, test, halo, haloooo, heyyyy, uy, oy, woy, on ga lu?, muncul kek, kmana sih lu, ilang mulu, eh, p, ppp, woi, kemana aja lu, sibuk ga lu, bales napa elah, heh, spada, nyariin ya, tes tes, yuhuuu, dor, lu idup ga?, woyy, assalamualaikum, jangan di read doang dong, kangen gw ya, halu, psst, eh lu tau ga, woi bangun",
    "laughter_and_amusement": "xixixi, wkwkwkwkwk, awokawok, haha, hahaha anjir, lol, lmao, ngakak guling guling, sakit perut gw ketawa, receh bgt tolong, humor gw anjlok, bengek hyung, ngakak brutal, wkwk random bgt, wk, kocak geming, ga kuat gw, nangis bgt wkwk, saking lucunya pengen meninggoy, perut gw kram, lawak lu, ada-ada aja anjir, kocak bgt sumpah, ngikngik, humor gw sebatas ini, jokes bapak2, lawak bgt anjir, ngakak sampe bengek, bisa aja lu, ampun deh wkwk",
    "affection_and_flirting": "lagi kangen tau, pengen ketemu, jalan berdua yuk, gemes bgt sih, salting brutal gw, baper tau, ayang, pagi ayang, jangan lupa makan ya, pengen peluk, pap dong, kgn u, miss u, luv u, mwa, lucu bgt sih lu, peluk onlen, kangen masa, ucul bgt, mleyot gw, pen gigit rasanya, sayangku, babe, jgn kemana-mana ya, soft bgt gila, bikin salting, caper bgt sih gw wkwk, gemoy, manja bgt ya gw, pengen dimanja, kangen peluk, miss u sekebon, hug online, jantung gw aman ga ya, meleleh gw, aaaa gemes, lu kok gemesin bgt sih, kgn, luvv",
    "anger_and_annoyance": "au ah gelap, terserah, gpp, bodo amat, males bgt gw, bete abis, mood gw anjlok, jangan ganggu gw dlu, nyebelin bgt sih, lu kenapa sih?, cowok emang gtu, red flag bgt gila, toxic anjir, ilfeel gw, dahlah, malesin bgt, sumbu pendek gw hari ini, emosi gw, ngeselin lu, cari ribut ya, ga mood sumpah, gajelas bgt asli, pengen gw tabok, astaga naga, dih, idih, najis, ew, cringe bgt, bikin emosi, kesel bgt, mau marah, bodo ah, yaudah sih, ribet lu, bacot, brisik, ngambek gw, awas aja lu, tandain ya, males ngetik, bct, gajelas lu kimay",
    "hunger_and_food": "laper bgt gila, perut gw bunyi nih, makan yuk, temenin makan dong, pengen yg manis manis, pengen eskrim, boba kuy, martabak manis keju enak kyknya, laper tpi diet, pesen gofood aja apa ya, ngemil apa ya enak, ngidam seblak, mie ayam enak nih kyknya, mulut gw asem pengen ngunyah, traktir dong, laper mata doang kyknya, cacing di perut gw udah demo, mau nangis saking lapernya, pengen nyemil, bucin makanan, gofood yuk, makan apa ya enaknya, kepingin martabak, laperrrrr, belum makan dari pagi, pengen ayam geprek, butuh asupan micin",
    "tiredness_and_laziness": "gw rebahan seharian, kaum rebahan check, males mandi, baru bangun gw wkwk, jam segini msh di kasur, yaudah deh gw mandi dlu, gw cabut dlu ya, mau makan dlu, good night, sweet dreams, mager parah, capek bgt fisik mental, pegel linu, pengen hibernasi, mata gw udah 5 watt, ngetik sambil merem nih, ketiduran anjir, ngantuk berat, skip dlu gw, ga kuat pengen molor, pegel bgt badan gw, jompo bgt gw, sakit pinggang, encok, mager gerak, pengen nempel kasur, capek batin, lemes bgt, butuh healing, kurang tidur gw, pengen resigndari kehidupan, capek woy",
    "gossip_and_curiosity": "eh dengerin gw mau cerita, ada hot tea nih, lu tau ga sih?, gw kasih tau ya tpi jgn cepu, si itu masa balikan lgi, gengsi dong, malu bgt sumpah, gw tdi kepeleset anjir, kuota gw sekarat, fyi aja nih, spill dong, eh masa iya?, kepo bgt gw, lu harus tau, eh gw liat pake mata kepala sendiri, valid no debat, parah ga sih, obrolan deep talk, julid dikit gpp kali ya, spill the tea, eh masa kemaren, lu tau gosip terbaru ga, kepo maksimal, jangan bilang siapa2 ya, sumpah gw syok denger ini, eh liat deh, gibah time, lambe turah mode on, lu harus dengerin gw",
    "agreement_and_confirmations": "anjir, anjay, bjir, buset, wkwk, hehe, hooh, hmmm, nah, tuh kan, yap, yoi, g, bisa jadi, masuk akal, bener jg, setuju gw, gaskeun, gas, sabi, mantap, keren bgt, valid, trs trs, nah iya, 100 buat lu, bener pisan, setuju 100%, sikat, oke oce, sepakat, bener kan kata gw, relate bgt, emang boleh se, nah bener, bener bgt, fakta, no kecot, gokil, keren parah, sabi lah, oke siap, sip, mantul, boleh jg, setuju parah, relate, hooh bgt, ya kan, bener kan dugaan gw",
    "surprise_and_disbelief": "sumpah?, demi apa?, seriusan?, masa?, boong, hoax lu, mana ada, agak laen emang, lu sehat?, stress lu ya, kok bisa?, emang iya?, terus lu jawab apa?, hah?, yg bener aja lu?, lahh, anjir kaget gw, di luar nurul, ga nyangka gw, plot twist bgt, speechless gw, merinding anjir, demi alek?, hah masa sih?, yg bener aja, loh kok gitu, diluar nalar, mindblowing, gila aja, astaga, ya ampun, serius lu?, wah parah sih, gak abis pikir gw, lah kocak, bisa gitu ya, kaget bgt anjir, ga ekspek gw"
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
        
    def add_memory(self, user_id: int, role: str, text: str):
        """
        Menyimpan interaksi (text) ke dalam memori.
        role bisa "user" atau "ai".
        """
        if not text.strip():
            return
            
        doc_id = f"mem_{user_id}_{int(time.time() * 1000)}"
        metadata = {"role": role, "timestamp": time.time(), "user_id": user_id}
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
    def search_memory(self, user_id: int, query: str, n_results: int = 1) -> list:
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
        user_docs = self.collection.get(where={"user_id": user_id})
        count = len(user_docs["ids"]) if user_docs and "ids" in user_docs else 0
        if count == 0:
            return []
            
        safe_n_results = min(n_results, count)
        
        results = self.collection.query(
            query_texts=[query],
            n_results=safe_n_results,
            where={"user_id": user_id}
        )
        
        memories = []
        # results["documents"][0] berisi list of document texts
        if results and "documents" in results and len(results["documents"]) > 0:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                role = meta.get("role", "unknown")
                memories.append(f"{role.upper()}: {doc}")
                
        return memories
