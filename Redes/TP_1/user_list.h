struct _user_cell{
	int user_id;
	struct _user_cell *next;
};
typedef struct _user_cell user_cell;

typedef struct{
    user_cell *start;
    user_cell *end;
}user_list;

void user_list_make_empty_list(user_list *l);
int user_list_is_list_empty(user_list *l);
void user_list_add_item_start(user_list *l, int user_id);
void user_list_add_item_end(user_list *l, int user_id);
void user_list_add_item_by_pointer(user_list *l, user_cell *item_before, int user_id);
user_cell *user_list_find(user_list *l, int user_id);
int user_list_remove_item_start(user_list *l);
int user_list_remove_item_end(user_list *l);
void user_list_remove_by_pointer(user_list *l, user_cell *item_before);
user_cell *user_list_get_first_item(user_list *l);
void user_list_print_list(user_list *l);
void user_list_free_list(user_list *l);