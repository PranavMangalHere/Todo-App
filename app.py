import streamlit as st

from todo.storage import add_task, load_tasks, save_tasks, set_task_completed

# Define the path to the CSV file
CSV_FILE = "tasks.csv"


def main():
    # Set the title of the web app
    st.title("To-Do List")
    st.markdown(
        """
         <style>
         .stApp {
             background-image: url("https://images.pexels.com/photos/2387793/pexels-photo-2387793.jpeg?cs=srgb&dl=pexels-adrien-olichon-2387793.jpg&fm=jpg");
             background-attachment: fixed;
             background-size: cover
         }
         </style>
         """,
        unsafe_allow_html=True,
    )

    # Load the tasks from the CSV file
    tasks = load_tasks(CSV_FILE)

    task_input = st.text_input("Add a new task:")
    if st.button("Add"):
        try:
            add_task(CSV_FILE, task_input)
            st.rerun()
        except ValueError:
            st.warning("Please enter a task.")
        except OSError:
            st.error("Unable to save tasks. Please try again.")

    display(tasks)

    if st.button("Clear all tasks"):
        try:
            save_tasks(CSV_FILE, [])
            st.rerun()
        except OSError:
            st.error("Unable to clear tasks. Please try again.")


def display(tasks):
    if len(tasks) == 0:
        st.write("No tasks added yet.")
        return

    st.write("Current tasks:")

    for task in tasks:
        checkbox_value = st.checkbox(task.title, value=task.completed, key=f"task_{task.id}")
        if checkbox_value != task.completed:
            try:
                set_task_completed(CSV_FILE, task.id, checkbox_value)
                st.rerun()
            except OSError:
                st.error("Unable to update task. Please try again.")


if __name__ == "__main__":
    main()
