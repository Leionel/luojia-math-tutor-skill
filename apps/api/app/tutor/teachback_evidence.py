"""Bind unverified model opinions to exact student spans; never assign a grade."""
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Span(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    start:int=Field(ge=0)
    end:int=Field(gt=0)
    quote:str=Field(min_length=1,max_length=4000)


class Opinion(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    condition_id:str=Field(max_length=100)
    judgment:Literal["supported","needs_followup","contradiction","unknown"]
    evidence:Span|None
    note:str=Field(min_length=1,max_length=300)
    followup:str=Field(min_length=1,max_length=300)


class Review(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    opinions:list[Opinion]=Field(min_length=1,max_length=10)


def original_spans(text,quote):
    if not quote:return []
    # Preserve every occurrence rather than guessing which identical sentence was meant.
    matches=[];offset=0
    while len(matches)<100:
        start=text.find(quote,offset)
        if start<0:break
        matches.append({'start':start,'end':start+len(quote),'quote':quote});offset=start+1
    return matches


def parse_review(answer,result):
    if len(answer)>20000:raise ValueError('review over budget')
    review=Review.model_validate(json.loads(answer))
    expected={row['condition_id'] for row in result['conditions']}
    ids=[row.condition_id for row in review.opinions]
    if len(set(ids))!=len(ids) or set(ids)!=expected:raise ValueError('condition identity mismatch')
    opinions={}
    for opinion in review.opinions:
        span=opinion.evidence
        if span and (span.end<=span.start or span.end>len(result['text']) or result['text'][span.start:span.end]!=span.quote):
            raise ValueError('student quote mismatch')
        if opinion.judgment in {'supported','contradiction'} and span is None:raise ValueError('judgment needs evidence')
        opinions[opinion.condition_id]={**opinion.model_dump(),'verified':False,'independent_success':False}
    return opinions
