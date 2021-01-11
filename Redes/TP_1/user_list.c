#include "user_list.h"
#include <stdlib.h>
#include <stdio.h>

void user_list_make_empty_list(user_list *l) {
    l->start = (user_cell *) malloc(sizeof(user_cell));
    l->end = l->start;
    l->start->next = NULL;
}

int user_list_is_list_empty(user_list *l) {
    return (l->start == l->end);
}

void user_list_add_item_start(user_list *l, int user_id) {
    user_cell *new_cell;
    new_cell = (user_cell *) malloc(sizeof(user_cell));
    l->start->user_id = user_id;
    new_cell->next = l->start;
    l->start = new_cell;
}

void user_list_add_item_end(user_list *l, int user_id) {
    l->end->next = (user_cell *) malloc(sizeof(user_cell));
    l->end = l->end->next;
    l->end->user_id = user_id;
    l->end->next = NULL;
}

void user_list_add_item_by_pointer(user_list *l, user_cell *item_before, int user_id) {
    user_cell *new_item = (user_cell *) malloc(sizeof(user_cell));
    new_item->user_id = user_id;
    new_item->next = item_before->next;
    item_before->next = new_item;

    if(item_before == l->end)
        l->end = new_item;
}

int user_list_remove_item_start(user_list *l) {
    if (user_list_is_list_empty(l))
        return 0;

    user_cell *p = l->start;
    l->start = l->start->next;
    free(p);
    return 1;
}

int user_list_remove_item_end(user_list *l) {
    if (user_list_is_list_empty(l))
        return 0;

    user_cell *p = l->start;
    while(p->next != l->end){
        p = p->next;
    }
    l->end = p;
    p = p->next;
    free(p);
    l->end->next = NULL;
    
    return 1;
}

//returns the pointer to 1 user_cell before the user_id
//if it don't exists, returns NULL
user_cell *user_list_find(user_list *l, int user_id) {
    user_cell *p = l->start;
    while (p->next != NULL) {
        if (p->next->user_id == user_id)
            return p;
        p = p->next;
    }
    return NULL;
}

void user_list_remove_by_pointer(user_list *l, user_cell *item_before){  
    if (item_before != NULL) {
        user_cell *user_id = item_before->next;
        if (user_id == l->end)
            l->end = item_before;
            
        item_before->next = user_id->next;
        free(user_id);
    }
}

user_cell *user_list_get_first_item(user_list *l) {
    return l->start->next;
}

void user_list_print_list(user_list *l) {
    user_cell *p = user_list_get_first_item(l);

    while (p != NULL) {
        printf("%d ", p->user_id);
        p = p->next;
    }
    printf("\n");
}

void user_list_free_list(user_list *l) {
    user_cell *p = l->start;

    while (p != NULL) {
        l->start = p->next;
        free(p);
        p = l->start;
    }
}