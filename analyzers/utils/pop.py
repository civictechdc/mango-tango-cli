def pop_unnecessary_fields(data):
    data.pop("base_analyzer")
    data.pop("factory")
    data.pop("api_factory")

    return data