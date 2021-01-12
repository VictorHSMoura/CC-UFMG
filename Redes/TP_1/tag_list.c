#include "tag_list.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

void tag_list_make_empty_list(tag_list *l) {
    l->start = (tag_cell *) malloc(sizeof(tag_cell));
    l->end = l->start;
    l->start->next = NULL;
}

int tag_list_is_list_empty(tag_list *l) {
    return (l->start == l->end);
}

void tag_list_add_item_start(tag_list *l, char *tag) {
    tag_cell *new_cell;
    new_cell = (tag_cell *) malloc(sizeof(tag_cell));
    
    l->start->tag = (char *) malloc((strlen(tag) + 1)*sizeof(char));
    memcpy(l->start->tag, tag, strlen(tag) + 1);
    l->start->tag[strlen(tag)] = '\0';
    user_list_make_empty_list(&l->start->users);
    
    new_cell->next = l->start;
    l->start = new_cell;
}

void tag_list_add_item_end(tag_list *l, char *tag) {
    l->end->next = (tag_cell *) malloc(sizeof(tag_cell));
    l->end = l->end->next;
    
    l->end->tag = (char *) malloc((strlen(tag) + 1)*sizeof(char));
    memcpy(l->end->tag, tag, strlen(tag) + 1);
    l->end->tag[strlen(tag)] = '\0';
    user_list_make_empty_list(&l->end->users);
    
    l->end->next = NULL;
}

void tag_list_add_item_by_pointer(tag_list *l, tag_cell *tag_before, char *tag) {
    tag_cell *new_item = (tag_cell *) malloc(sizeof(tag_cell));
    
    new_item->tag = (char *) malloc((strlen(tag) + 1)*sizeof(char));
    memcpy(new_item->tag, tag, strlen(tag) + 1);
    new_item->tag[strlen(tag)] = '\0';
    user_list_make_empty_list(&new_item->users);
    
    new_item->next = tag_before->next;
    tag_before->next = new_item;

    if(tag_before == l->end)
        l->end = new_item;
}

int tag_list_remove_item_start(tag_list *l) {
    if (tag_list_is_list_empty(l))
        return 0;

    tag_cell *p = l->start;
    l->start = l->start->next;
    free(p);
    return 1;
}

int tag_list_remove_item_end(tag_list *l) {
    if (tag_list_is_list_empty(l))
        return 0;

    tag_cell *p = l->start;
    while(p->next != l->end){
        p = p->next;
    }
    l->end = p;
    p = p->next;
    free(p);
    l->end->next = NULL;
    
    return 1;
}

//returns the pointer to 1 tag_cell before the tag
//if it don't exists, returns NULL
tag_cell *tag_list_find(tag_list *l, char *tag) {
    tag_cell *p = l->start;
    while (p->next != NULL) {
        if (strcmp(p->next->tag, tag) == 0)
            return p;
        p = p->next;
    }
    return NULL;
}

void tag_list_remove_by_pointer(tag_list *l, tag_cell *tag_before){  
    if (tag_before != NULL) {
        tag_cell *tag = tag_before->next;
        if (tag == l->end)
            l->end = tag_before;
            
        tag_before->next = tag->next;
        free(tag);
    }
}

tag_cell *tag_list_get_first_item(tag_list *l) {
    return l->start->next;
}

tag_cell *tag_list_get_last_item(tag_list *l) {
    return l->end;
}

void tag_list_print_list(tag_list *l) {
    tag_cell *p = tag_list_get_first_item(l);

    while (p != NULL) {
        printf("%s\n", p->tag);
        p = p->next;
    }
}

void tag_list_free_list(tag_list *l) {
    tag_cell *p = l->start;

    while (p != NULL) {
        l->start = p->next;
        free(p);
        p = l->start;
    }
}