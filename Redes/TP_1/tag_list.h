#include "user_list.h"

struct _tag_cell{
	char *tag;
    user_list *users;
	struct _tag_cell *next;
};
typedef struct _tag_cell tag_cell;

typedef struct{
    tag_cell *start;
    tag_cell *end;
}tag_list;

void tag_list_make_empty_list(tag_list *l);
int tag_list_is_list_empty(tag_list *l);
void tag_list_add_item_start(tag_list *l, char *tag);
void tag_list_add_item_end(tag_list *l, char *tag);
void tag_list_add_item_by_pointer(tag_list *l, tag_cell *tag_before, char *tag);
tag_cell *tag_list_find(tag_list *l, char *tag);
int tag_list_remove_item_start(tag_list *l);
int tag_list_remove_item_end(tag_list *l);
void tag_list_remove_by_pointer(tag_list *l, tag_cell *tag_before);
tag_cell *tag_list_get_first_item(tag_list *l);
void tag_list_print_list(tag_list *l);
void tag_list_free_list(tag_list *l);