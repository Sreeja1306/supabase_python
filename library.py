import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
url = os.getenv("supabaseUrl")
key = os.getenv("supabaseKey")
sb: Client = create_client(url, key)

def add_member():
    name = input("Enter member name: ").strip()
    email = input("Enter member email: ").strip()
    resp = sb.table("members").insert({"name": name, "email": email}).execute()
    print("Inserted Member:", resp.data)

def add_book():
    title = input("Enter book title: ").strip()
    author = input("Enter book author: ").strip()
    category = input("Enter book category: ").strip()
    stock = int(input("Enter stock count: ").strip())
    resp = sb.table("books").insert({
        "title": title, "author": author, "category": category, "stock": stock
    }).execute()
    print("Inserted Book:", resp.data)

def list_books():
    books = sb.table("books").select("*").execute().data
    print("Books in Library:")
    for b in books:
        print(f"ID:{b['book_id']} Title:{b['title']} Author:{b['author']} "
              f"Category:{b['category']} Stock:{b['stock']}")

def search_books():
    choice = input("Search by (title/author/category): ").strip().lower()
    keyword = input("Enter keyword: ").strip()
    if choice in ("title", "author", "category"):
        books = sb.table("books").select("*").ilike(choice, f"%{keyword}%").execute().data
        print("Search Results:")
        for b in books:
            print(f"ID:{b['book_id']} Title:{b['title']} Author:{b['author']} "
                  f"Category:{b['category']} Stock:{b['stock']}")
    else:
        print("Invalid search type")

def member_with_books():
    member_id = int(input("Enter member ID: ").strip())
    member = sb.table("members").select("*").eq("member_id", member_id).execute().data
    borrowed = sb.table("borrow_records").select("book_id, borrow_date, return_date")\
        .eq("member_id", member_id).execute().data
    print("Member:", member)
    print("Borrowed Books:", borrowed)

def update_book_stock():
    book_id = int(input("Enter book ID to update stock: ").strip())
    new_stock = int(input("Enter new stock value: ").strip())
    resp = sb.table("books").update({"stock": new_stock}).eq("book_id", book_id).execute()
    print("Updated Book:", resp.data)

def update_member_email():
    member_id = int(input("Enter member ID to update email: ").strip())
    new_email = input("Enter new email: ").strip()
    resp = sb.table("members").update({"email": new_email}).eq("member_id", member_id).execute()
    print("Updated Member:", resp.data)

def delete_member():
    member_id = int(input("Enter member ID to delete: ").strip())
    # Check if borrowed books exist
    borrowed = sb.table("borrow_records").select("*").eq("member_id", member_id).is_("return_date", None).execute().data
    if borrowed:
        print("Cannot delete member. Books still borrowed.")
        return
    resp = sb.table("members").delete().eq("member_id", member_id).execute()
    print("Deleted Member:", resp.data)

def delete_book():
    book_id = int(input("Enter book ID to delete: ").strip())
    borrowed = sb.table("borrow_records").select("*").eq("book_id", book_id).is_("return_date", None).execute().data
    if borrowed:
        print("Cannot delete book. Currently borrowed by member(s).")
        return
    resp = sb.table("books").delete().eq("book_id", book_id).execute()
    print("Deleted Book:", resp.data)

def borrow_book():
    member_id = int(input("Enter member ID: ").strip())
    book_id = int(input("Enter book ID: ").strip())
    book = sb.table("books").select("*").eq("book_id", book_id).execute().data
    if not book:
        print("Book not found")
        return
    if book[0]["stock"] <= 0:
        print("Book not available")
        return
    # Transaction
    sb.table("borrow_records").insert({"member_id": member_id, "book_id": book_id}).execute()
    sb.table("books").update({"stock": book[0]["stock"] - 1}).eq("book_id", book_id).execute()
    print("Book borrowed successfully")

def return_book():
    member_id = int(input("Enter member ID: ").strip())
    book_id = int(input("Enter book ID: ").strip())
   
    borrow = sb.table("borrow_records").select("*")\
        .eq("member_id", member_id).eq("book_id", book_id).is_("return_date", None).execute().data
    if not borrow:
        print("No active borrow record found")
        return
    record_id = borrow[0]["record_id"]
    sb.table("borrow_records").update({"return_date": datetime.now().isoformat()}).eq("record_id", record_id).execute()
    
    book = sb.table("books").select("*").eq("book_id", book_id).execute().data
    sb.table("books").update({"stock": book[0]["stock"] + 1}).eq("book_id", book_id).execute()
    print("Book returned successfully")

def top_5_books():
    sql = """SELECT b.title, b.author, COUNT(*) as borrow_count 
             FROM borrow_records br 
             JOIN books b ON br.book_id = b.book_id
             GROUP BY b.title, b.author 
             ORDER BY borrow_count DESC LIMIT 5;"""

    print("Top 5 borrowed books: (Raw SQL may require PostgREST client)")

def overdue_members():
    threshold = (datetime.now() - timedelta(days=14)).isoformat()
    print("Members with overdue books >14 days: (Raw SQL may require PostgREST client)")

def total_borrowed_per_member():
    print("Total books borrowed per member: (Raw SQL may require PostgREST client)")
menu = {
    "1": add_member,
    "2": add_book,
    "3": list_books,
    "4": search_books,
    "5": member_with_books,
    "6": borrow_book,
    "7": return_book,
    "8": update_book_stock,
    "9": update_member_email,
    "10": delete_member,
    "11": delete_book,
    "12": top_5_books,
    "13": overdue_members,
    "14": total_borrowed_per_member
}

if __name__ == "__main__":
    while True:
        print("\n--- Library Menu ---")
        print("1.Add Member 2.Add Book 3.List Books 4.Search Books 5.Show Member & Borrowed")
        print("6.Borrow Book 7.Return Book 8.Update Book Stock 9.Update Member Email")
        print("10.Delete Member 11.Delete Book 12.Top 5 Borrowed 13.Overdue Members 14.Total Borrowed per Member")
        print("0.Exit")
        choice = input("Enter choice: ").strip()
        if choice == "0":
            break
        func = menu.get(choice)
        if func:
            func()
        else:
            print("Invalid choice")
